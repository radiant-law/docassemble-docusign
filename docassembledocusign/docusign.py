import requests 
import time
import jwt
import json
import base64
import hashlib
import re

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

class EnvelopeCreator:
    """Class for creating envelopes"""

    def __init__(self, integrator_key, user_id, private_key):
        current_time = int(time.time())
        hour_later = int(time.time()) + 3600
        self.jwt_code = jwt.encode({
            'iss': integrator_key,
            'sub': user_id,
            'iat': current_time,
            'exp': hour_later,
            'aud': 'account-d.docusign.com',
            'scope': 'signature impersonation'
        }, private_key, algorithm='RS256')

    def create_envelope(self, recipients, documents, send_immediately=False, email_subject="Please Sign", assign_doc_ids=True, assign_recipient_ids=True, production=False):
        """Creates an envelope and prepares it to be sent to a number of recipients."""
        # Check received recipients are okay whilst rotating the format to fix Docusign API
        rotated_recipients = {}
        for index, recipient in enumerate(recipients):
            if 'name' not in recipient.keys():
                raise ValueError("Missing 'name' in recipient")
            if 'email' not in recipient.keys():
                raise ValueError("Missing 'email' in recipient")
            if 'routingOrder' not in recipient.keys():
                raise ValueError("Missing 'routingOrder' in recipient")
            else:
                if not re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", recipient['email']):
                    raise ValueError("Email incorrectly formatted")
            if assign_recipient_ids:
                recipient['recipientId'] = index + 1
            elif 'recipientId' not in recipient.keys():
                raise ValueError("Missing 'recipientId' in recipient whilst assign_recipient_ids is False")
            if 'tabs' in recipient.keys():
                rotated_tabs = {}
                for tab in recipient['tabs']:
                    if 'type' not in tab.keys():
                        raise ValueError("Missing 'type' in tab")
                    tab_type = tab['type']
                    tab_type_extended = tab_type + 'Tabs'
                    del tab['type']
                    if tab_type not in TAB_TYPES.keys():
                        raise ValueError("Invalid tab type")
                    if not TAB_TYPES[tab_type]['set_value']:
                        if not all(key not in tab.keys() for key in ['locked', 'originalValue']):
                            raise ValueError("Value cannot be controlled for this tab type")
                    if tab_type_extended not in rotated_tabs.keys():
                        rotated_tabs[tab_type_extended] = [tab]
                    else:
                        rotated_tabs[tab_type_extended].append(tab)
                del recipient['tabs']
                recipient['tabs'] = rotated_tabs
            if 'group' not in recipient.keys():
                raise ValueError("Missing 'group' in recipient")
            recipient_group = recipient['group']
            del recipient['group']
            if recipient_group not in rotated_recipients.keys():
                rotated_recipients[recipient_group] = [recipient]
            else:
                rotated_recipients[recipient_group].append(recipient)
        
        # Check received documents are okay whilst assigning ids if asked to
        for index, document in enumerate(documents):
            if 'name' not in document.keys():
                raise ValueError("Missing 'name' in document")
            if 'fileExtension' not in document.keys():
                raise ValueError("Missing 'fileExtension' in document")
            if assign_doc_ids:
                document['documentId'] = index + 1
            elif 'documentId' not in document.keys():
                raise ValueError("Missing 'documentId' in document whilst assign_doc_ids is False")
            if 'documentBase64' not in document.keys():
                raise ValueError("Missing 'documentBase64' in document")
        
        # Build our request json
        if send_immediately:
            status = "sent"
        else:
            status = "created"
        request_json = {
            'status': status,
            'emailSubject': email_subject,
            'recipients': rotated_recipients,
            'documents': documents
        }
        
        # Authenticate
        if production:
            base_uri = "https://account.docusign.com"
        else:
            base_uri = "https://account-d.docusign.com"
        request_for_token = requests.post(base_uri + '/oauth/token', data={
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'assertion': self.jwt_code
        })
        token = json.loads(request_for_token.text)['access_token']
        authorization_header = {'Authorization': 'Bearer ' + token}
        request_for_user = requests.get(base_uri + '/oauth/userinfo', headers=authorization_header)
        account_id = json.loads(request_for_user.text)['accounts'][0]['account_id']
        base_uri = json.loads(request_for_user.text)['accounts'][0]['base_uri']
        extended_base_uri = base_uri + '/restapi/v2/accounts/' + account_id
        
        # Send off envelope request and return the results
        envelope = requests.post(extended_base_uri + '/envelopes', headers=authorization_header, json=request_json)
        envelope.raise_for_status()
        return request_json, json.loads(envelope.text), envelope.status_code

def make_document_base64(document_path):
    """Converts your document from document_path to a base64 string, as used by Docusign"""
    with open(document_path, 'rb') as document:
        return base64.b64encode(document.read()).decode('utf-8')
        
def generate_anchor(tab_type, email):
    """Generate standard anchor using SHA1 hash of email and standard abbreviation"""
    return hashlib.sha1(email.encode('utf-8')).hexdigest()[:10] + '-' + TAB_TYPES[tab_type]['abbreviation']
