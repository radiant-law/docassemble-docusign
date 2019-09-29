# DocuSign Integration for Docassemble

import requests 
import time
import jwt
import json
import base64
import hashlib
import re
from docassemble.base.util import DAError, log, interview_url, DAObject, defined, get_config, all_variables, DARedis, user_info, url_of

__all__ = ['DocuSign','generate_anchor','make_document_base64']

RECIPIENT_TYPES = {
    'agents': {},
    'carbonCopies': {},
    'certifiedDeliveries': {},
    'editors': {},
    'inPersonSigners': {},
    'intermediaries': {},
    'seals': {},
    'signers': {}
}

TAB_TYPES = {
    'approve': {'abbreviation': 'appro', 'set_value': False},
    'checkbox': {'abbreviation': 'check', 'set_value': True},
    'company': {'abbreviation': 'compa', 'set_value': False},
    'dateSigned': {'abbreviation': 'dates', 'set_value': False},
    'date': {'abbreviation': 'datex', 'set_value': True},
    'decline': {'abbreviation': 'decli', 'set_value': False},
    'email': {'abbreviation': 'email', 'set_value': True},
    'envelopeId': {'abbreviation': 'envel', 'set_value': False},
    'firstName': {'abbreviation': 'first', 'set_value': False},
    'formulaTab': {'abbreviation': 'formu', 'set_value': True},
    'fullName': {'abbreviation': 'fulln', 'set_value': False},
    'initialHere': {'abbreviation': 'initi', 'set_value': False},
    'lastName': {'abbreviation': 'lastn', 'set_value': False},
    'list': {'abbreviation': 'list', 'set_value': True},
    'notarize': {'abbreviation': 'notar', 'set_value': True},
    'note': {'abbreviation': 'note', 'set_value': True},
    'number': {'abbreviation': 'numbe', 'set_value': True},
    'radioGroup': {'abbreviation': 'radio', 'set_value': True},
    'signHere': {'abbreviation': 'signh', 'set_value': False},
    'signerAttachment': {'abbreviation': 'signe', 'set_value': False},
    'ssn': {'abbreviation': 'ssn', 'set_value': True},
    'text': {'abbreviation': 'text', 'set_value': True},
    'title': {'abbreviation': 'title', 'set_value': False},
    'view': {'abbreviation': 'view', 'set_value': True},
    'zip': {'abbreviation': 'zip', 'set_value': True}
}

class DocuSign:
    def __init__(self, auth_only=False, *pargs, **kwargs):
        # Parameters
        # auth_only indicates that the interview is creating the object for authorization only,
        # and so it will not check for any configuration data beyond client_id and test_mode.
        
        # Get Server Configuration
        if auth_only:
            self.get_server_config(auth_only=True)
        else:
            self.get_server_config()
          
        self.target_uri = url_of('interview', _external=True)
      
      
    def get_server_config(self,auth_only=False):
        # auth_only allows you to grab only the client-id from the configuration for the
        # purpose of running authentication requests.
        
        docusign_configuration = get_config('docusign')
        if not docusign_configuration:
            raise DAError("Attempt to read DocuSign configuration failed. DocuSign is not configured for the server.")
        else:
            #Import the client_ID or throw an error.
            if 'client-id' in docusign_configuration:
                self.client_id = docusign_configuration['client-id']
            else:
                raise DAError("DocuSign configuration does not include client-id.")
            if 'test-mode' in docusign_configuration:
                self.test_mode = docusign_configuration['test-mode']
            else:
                raise DAError("DocuSign configuration does not include test-mode.")
            if not auth_only:
                # Get the rest of the required configuration variables here.
                if 'impersonated-user-guid' in docusign_configuration:
                    self.impersonated_user_guid = docusign_configuration['impersonated-user-guid']
                else:
                    raise DAError("DocuSign confinguration does not include impersonated-user-guid.")
                if 'private-key' in docusign_configuration:
                    self.private_key = docusign_configuration['private-key']
                else:
                    raise DAError("DocuSign configuration does not include private-key.")
            
        
    def authorization_link(self):
        if self.test_mode:
            base_url = "https://account-d.docusign.com/oauth/auth"
        else:
            base_url = "https://account.docusign.com/oauth/auth"
        url = base_url + "?response_type=code&scope=signature%20impersonation&client_id="
        url += self.client_id
        url += "&redirect_uri="
        url += url_of('interview', _external=True)
        #log("URL Generated: " + url, "info")
        return url

    def get_token(self):
        if self.test_mode:
            aud = "account-d.docusign.com"
            base_uri = "https://account-d.docusign.com"
        else:
            aud = "account.docusign.com"
            base_uri = "https://account.docusign.com"
        current_time = int(time.time())
        hour_later = int(time.time()) + 3600
        self.jwt_code = jwt.encode({
            'iss': self.client_id,
            'sub': self.impersonated_user_guid,
            'iat': current_time,
            'exp': hour_later,
            'aud': aud,
            'scope': 'signature impersonation'
        }, self.private_key, algorithm='RS256')
        request_for_token = requests.post(base_uri + '/oauth/token', data={
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'assertion': self.jwt_code
        })
        self.token = json.loads(request_for_token.text)['access_token']
    
    def get_user_info(self):
        if self.test_mode:
            base_uri = "https://account-d.docusign.com"
        else:
            base_uri = "https://account.docusign.com"
        self.authorization_header = {'Authorization': 'Bearer ' + self.token}
        request_for_user = requests.get(base_uri + '/oauth/userinfo', headers=self.authorization_header)
        user_account_id = json.loads(request_for_user.text)['accounts'][0]['account_id']
        user_base_uri = json.loads(request_for_user.text)['accounts'][0]['base_uri']
        self.extended_base_uri = user_base_uri + '/restapi/v2/accounts/' + user_account_id
      
    def test_api_connection(self):
        # This function just tests whether authentication works well enough to obtain the user's
        # specific server and account ID, as required in the last step of JWT authentication.
        # If it outputs '/restapi/v2/accounts/' authentication is not working.
        # If it outputs 'https://server.address/restapi/v2/accounts/client-id' then it is working.
        
        self.get_token()
        self.get_user_info()
        return self.extended_base_uri

    def get_signatures(self, recipients, documents, custom_fields=[], send_immediately=False, email_subject="Please Sign", assign_doc_ids=True, assign_recipient_ids=True, assign_field_ids=True):
        """Creates an envelope and prepares it to be sent to a number of recipients."""
        # Check received recipients are okay whilst rotating the format to fix Docusign API
        rotated_recipients = {}
        for index, recipient in enumerate(recipients):
            if 'name' not in recipient.keys():
                raise DAError("Missing 'name' in recipient")
            if 'email' not in recipient.keys():
                raise DAError("Missing 'email' in recipient")
            if 'routingOrder' not in recipient.keys():
                raise DAError("Missing 'routingOrder' in recipient")
            else:
                if not re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", recipient['email']):
                    raise DAError("Email incorrectly formatted")
            if assign_recipient_ids:
                recipient['recipientId'] = index + 1
            elif 'recipientId' not in recipient.keys():
                raise DAError("Missing 'recipientId' in recipient whilst assign_recipient_ids is False")
            if 'tabs' in recipient.keys():
                rotated_tabs = {}
                for tab in recipient['tabs']:
                    if 'type' not in tab.keys():
                        raise DAError("Missing 'type' in tab")
                    tab_type = tab['type']
                    tab_type_extended = tab_type + 'Tabs'
                    del tab['type']
                    if tab_type not in TAB_TYPES.keys():
                        raise DAError("Invalid tab type")
                    if not TAB_TYPES[tab_type]['set_value']:
                        if not all(key not in tab.keys() for key in ['locked', 'originalValue']):
                            raise DAError("Value cannot be controlled for this tab type")
                    if tab_type_extended not in rotated_tabs.keys():
                        rotated_tabs[tab_type_extended] = [tab]
                    else:
                        rotated_tabs[tab_type_extended].append(tab)
                del recipient['tabs']
                recipient['tabs'] = rotated_tabs
            if 'group' not in recipient.keys():
                raise DAError("Missing 'group' in recipient")
            recipient_group = recipient['group']
            del recipient['group']
            if recipient_group not in rotated_recipients.keys():
                rotated_recipients[recipient_group] = [recipient]
            else:
                rotated_recipients[recipient_group].append(recipient)
          
        # Check received documents are okay whilst assigning ids if asked to
        for index, document in enumerate(documents):
            if 'name' not in document.keys():
                raise DAError("Missing 'name' in document")
            if 'fileExtension' not in document.keys():
                raise DAError("Missing 'fileExtension' in document")
            if assign_doc_ids:
                document['documentId'] = index + 1
            elif 'documentId' not in document.keys():
                raise DAError("Missing 'documentId' in document whilst assign_doc_ids is False")
            if 'documentBase64' not in document.keys():
                raise DAError("Missing 'documentBase64' in document")
          
        # Check received envelope custom fields and rotate format
        rotated_fields = {'listCustomFields': [], 'textCustomFields': []}
        for index, field in enumerate(custom_fields):
            if assign_field_ids:
                field['fieldId'] = index + 1
            elif 'fieldId' not in field.keys():
                raise DAError("Missing 'fieldId' in field whilst assign_field_ids is False")
            if 'type' not in field.keys():
                raise DAError("Missing 'type' in custom field")
            if field['type'] == 'list':
                del field['type']
                rotated_fields['listCustomFields'].append(field)
            elif field['type'] == 'text':
                del field['type']
                rotated_fields['textCustomFields'].append(field)
            else:
                raise DAError("Invalid custom field type")

        # Build our request json
        if send_immediately:
            status = "sent"
        else:
            status = "created"
        request_json = {
            'status': status,
            'emailSubject': email_subject,
            'recipients': rotated_recipients,
            'documents': documents,
            'envelopecustomFields': rotated_fields
        }
        
        # Send off envelope request and return the results
        if send_immediately:
            self.get_token()
            self.get_user_info()
            envelope = requests.post(self.extended_base_uri + '/envelopes', headers=self.authorization_header, json=request_json)
            envelope.raise_for_status()
            return request_json, json.loads(envelope.text), envelope.status_code
        else:
            return request_json

def make_document_base64(document_path):
    """Converts your document from document_path to a base64 string, as used by Docusign"""
    with open(document_path, 'rb') as document:
        return base64.b64encode(document.read()).decode('utf-8')
        
def generate_anchor(tab_type, email, uid=''):
    """Generate standard anchor using SHA1 hash of email and standard abbreviation"""
    return hashlib.sha1(email.encode('utf-8')).hexdigest()[:10] + TAB_TYPES[tab_type]['abbreviation'] + uid
