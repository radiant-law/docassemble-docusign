# docassemble.docusign

A docassemble extension to allow you to access the DocuSign API from inside Docassemble interviews.

## Installation

Install this package from within your Docassemble package management screen using the GitHub address.

## Configuration

Docassemble-DocuSign uses the JWT authorization technique.  See the DocuSign API Documentation for details.

To configure Docassemble to access your DocuSign account:

1. In the DocuSign Admin system, create a docassemble-docusign app.
2. Create an RSA Keypair for that app, and save the private key to a secure location.
3. For that app, add https://{your.server.here}/interview as a redirect URI, or whatever your "interview" root is on your
   docassemble server.
4. Get the integration key or "client ID" for your app.
5. In the user section of your DocuSign admin system, look at the details of the user account your app will use, and get
   the "API Username" for that user.
   
Now you are ready to configure docassemble-docusign. Go into the configuration screen of docassemble, and add the following
configuration lines. Remember that whitespace matters.

```
docusign:
  client-id: {the integration key or client ID from step 4}
  impersonated-user-guid: {the API Username from step 5}
  test-mode: True
  private-key: |
    -----BEGIN RSA PRIVATE KEY-----
    {the private key you saved from step 2}
    -----END RSA PRIVATE KEY-----
```

### Test Mode
If you set `test-mode: True`, the extension will use sandbox mode on the DocuSign API.
If you set `test-mode: False`, the extension will use live mode on the DocuSign API.

## Authenticating

Now the extension is configured, but you need to give it permission to impersonate the DocuSign user account.

To do that run the `docusign_auth.yml` interview included with the package. It will send you to the right location to authorize.

## Usage

### Include the Module

First, include the module in your interview.

```
---
modules:
  - docassemble.docusign.da_docusign
---
```

### Generate DocuSign Tabs

Second, use the `generate_anchor` function to insert "Anchors" into your document where you want DocuSign tabs to appear.

`generate_anchor` accepts two parameters, the first is a DocuSign anchor type, which must be one of:

* 'approve'
* 'checkbox'
* 'company'
* 'dateSigned'
* 'date'
* 'decline'
* 'email'
* 'envelopeId'
* 'firstName'
* 'formulaTab'
* 'fullName'
* 'initialHere'
* 'lastName'
* 'list'
* 'notarize'
* 'note'
* 'number'
* 'radioGroup'
* 'signHere'
* 'signerAttachment'
* 'ssn'
* 'text'
* 'title'
* 'view'
* 'zip'

The second parameter is the email address of the person who needs to fill out that tab.

For example, you can create a template in your docassemble interview as follows:

```
attachments:
  - name: Your Document
    filename: docusign_test_doc
    variable name: docusign_test_doc
    content: |
      % for r in recipient:
      
      ${ generate_anchor('signHere', r.email) }  
        
      ***  
        
      ${ r.name }
      ${ generate_anchor('date', r.email) }
      % endfor
```

That code will generate an anchor for the signature, followed by a horizontal line, followed by the person's name, followed by an
anchor for the date on which they signed the document.

### Create the DocuSign Envelope Parameters

Next, your code needs to create a Python object for the recipients portion of the DocuSign envelope, and a python object for the
documents portion of the DocuSign Envelope.

Note that when you are generating your recipients object, you must include all the same tabs that you generated anchors for in the
document, to ensure that DocuSign will deal properly with them. When generating tabs, use the `generate_anchor` function.

An example of a correctly formated recipients object is:

```
recipients=[
        {
            'name': 'Doug Rattman',
            'email': 'doug.rattman@aperturescience.com',
            'group': 'signers',
            'routingOrder': 1,
            'tabs': [
                {
                    'type': 'signHere',
                    'anchorString': generate_anchor('signHere', 'doug.rattman@aperturescience.com')
                },
                {
                    'type': 'date',
                    'anchorString': generate_anchor('date', 'doug.rattman@aperturescience.com')
                }
            ]
        },
        {
            'name': 'Cave Johnson',
            'email': 'ceo@aperturescience.com',
            'group': 'certifiedDeliveries',
            'routingOrder': 2
        }
    ]
```

See the DocuSign API documentation for information on the features that are available in DocuSign envelopes.

When generating documents, use the `make_document_base64` function to convert the document to Base64 before adding it to the object.

`make_document_base64` accepts a path to a document. If you want to use a dynamically-generated document in a Docassemble interview,
give that document a `variable name:` attribute, and then use `document_variable_name.pdf.path()`, replacing `pdf` with whatever
document format you prefer.

An example of a correctly formatted documents object is:

```
documents=[
        {
            'name': "Bring Your Daughter To Work Day",
            'fileExtension': 'docx',
            'documentBase64': make_document_base64('bydtwd.docx')
        },
        {
            'name': "Lemon Grenade Acquisition",
            'fileExtension': 'docx',
            'documentBase64': docasign.make_document_base64('lemongrenadeacquisition.docx')
        }
    ]
```

There is an example interview provided in the package, `docusign_test_interview.yml`, that has an example of generating the
recipient and document objects in code.

### Send the Envelope to DocuSign

In your interview code, create a DocuSign() object:

```
code: |
  ds = DocuSign()
```

Then, call the `get_signatures()` function to send your documents to your recipients.

`get_signatures` accepts the following parameters:
* `recipients`: Mandatory. The recipients object described above.
* `documents`: Mandatory. The documents object described above.
* `send_immediately`: Optional, if set to `True`, your request will be sent. If `False`, 
* `email_subject`: optional, defaults to "Please Sign".
* `assign_doc_ids`: optional, deafults to `True`. Set to `False` if you are manually setting document IDs in your document object.
* `assign_recipient_ids`: optional, deafaults to `True`. Set to `False` if you are manually setting recipient IDs in your recipients object.

`get_signatures` returns the JSON formatted version of your DocuSign envelope when `send_immediately` is `False`.
If `send_immediately` is set to `True`, then it returns three values:

* the JSON formatted version of the DocuSign envelope
* the response data of the DocuSign Server
* the status code of the request to the DocuSign Server

A successful envelope submission will return a status code of 201.
