# docassemble-docusign

Python docassemble module for integrating with DocuSign. More specifically, it provides a simple way to create and send envelopes with standards for anchor text that must be placed in your document.

## How to use

The module is built around one magical method, `create_envelope`, on one magical class, `EnvelopeCreator`. The function takes more arguments that would normally be palatable, however, it needs to be passed three different DocuSign credentials, which can be stored (JASON HELP HERE) and recalled as (JASON PLEASE).

Before all this, you must create an integration key. This can be found in the DocuSign admin section, where you will also find your USER_ID, which we will need later.

The first step is to obtain consent from the user you will be impersonating, as is generally polite. You need to open a web browser up to:

```
https://account-d.docusign.com/oauth/auth?
response_type=token
&scope=signature%20impersonation
&client_id=YOUR_INTEGRATION_KEY
&redirect_uri=YOUR_REDIRECT_URI
```

That should be all one line like a normal URL, it's just formatted like that to show what the different parts are. The redirect URI isn't necessarily important as something to catch data to, but it must be specified along with your integration key, or DocuSign will freak out. Oh, and if you're on production, it's instead `https://account.docusign.com`.

Here's some sample code, we'll go through it part by part afterwards.

```python
import docassemble-docusign as docasign

envelope_creator = docasign.EnvelopeCreator(
    integrator_key='INTEGRATOR KEY HERE',
    user_id='USER ID HERE',
    private_key='PRIVATE KEY HERE'
)

envelope_creator.create_envelope(
    recipients=[
        {
            'name': 'Doug Rattman',
            'email': 'doug.rattman@aperturescience.com',
            'group': 'signers',
            'routingOrder': 1,
            'tabs': [
                {
                    'type': 'signHere',
                    'anchorString': docasign.generate_anchor('signHere', 'doug.rattman@aperturescience.com')
                },
                {
                    'type': 'date',
                    'anchorString': docasign.generate_anchor('date', 'doug.rattman@aperturescience.com')
                }
            ]
        },
        {
            'name': 'Cave Johnson',
            'email': 'ceo@aperturescience.com',
            'group': 'certifiedDeliveries',
            'routingOrder': 2
        }
    ],
    documents=[
        {
            'name': "Bring Your Daughter To Work Day",
            'fileExtension': 'docx',
            'documentBase64': docasign.make_document_base64('bydtwd.docx')
        },
        {
            'name': "please bring coffee up to my office",
            'fileExtension': 'docx',
            'documentBase64': docasign.make_document_base64('ineedcoffeenow.docx')
        }
    ],
    send_immediately=True,
    email_subject="Very Important Documents To Sign",
    production=True,
    assign_recipient_ids=True,
    assign_doc_ids=True
)
```

Okay, one at a time.

First, we import `docassemble-docusign` as `docasign` (it's a portmanteau), and create an `EnvelopeCreator`:

```python
import docassemble-docusign as docasign

envelope_creator = docasign.EnvelopeCreator(
    integrator_key='INTEGRATOR KEY HERE',
    user_id='USER ID HERE',
    private_key='PRIVATE KEY HERE'
)
```

Now we run the method. Let's look at those arguments one at a time, starting with the `recipients`. You will essentially be passing a list of dictionaries, each of which represent a single recipient. It's important to note that this only lists the bare minimum; any additional key-value pairs in the [DocuSign REST API](https://developers.docusign.com/esign-rest-api) can be included into any of the dictionaries you pass without hassle (or at least, there shouldn't be... look, it's a huge API, okay!)

Key | Value
--- | ---
`'name'` | Name of recipient
`'email'` | Email address of recipient
`'group'` | Type of recipient, must be part of: `'agents'`, `'carbonCopies'`, `'certifiedDeliveries'`, `'editors'`, `'inPersonSigners'`, `'intermediaries'`, `'seals'`, `'signers'`. For more details, [read this](https://developers.docusign.com/esign-rest-api/guides/concepts/recipients).
`'routingOrder'` | Order in which recipients receive the envelope. All of routing order 1 must complete their task (usually sign) before routing order 2, who must complete before 3, and so on.
`'tabs'` | See below...

We're going to talk about tabs at the end, because they require additional work put into your own documents that you will create in docassemble. Instead, let's look at the `documents` argument now. Like `recipients`, you'll be passing a list of dictionaries, each of which represent one document. Every document needs three key-value pairs:

Key | Value
--- | ---
`'name'` | Name of document
`'fileExtension'` | File extension of the document (such as `'pdf'` or `'docx'`)
`'documentBase64'` | A base64 encoding of your document; can be generated with the `make_document_base64` function, as seen above

Finally, there are some optional arguments...

Argument | Effect
--- | ---
`send_immediately` | If `True`, sends envelope immediately, otherwise saves envelope as draft. Defaults to `False`.
`email_subject` | Subject of email sent to recipients. Defaults to `"Please Sign"`.
`production` | If `True`, uses production server, otherwise uses the sandbox. Defaults to `False`.
`assign_recipient_ids` | Normally the API requires every recipient to have their own arbritrary id. If set to `True`, this is done for you. Defaults to `True`.
`assign_doc_ids` | Same deal as `assign_recipient_ids`. Seriously, unless you have something fancy in mind, leave this on. Defaults to `True`.

### Tabs

If you don't want your signers to be allowed to scribble whatever wherever on the document (known as 'free-form signing'), you'll need to define some tabs. Tabs are the bits you either click on or type on in order to sign a document, for example, a signature box or a text field, as well as some tabs that have locked values, such as one that displays the date signed. There are a scary number of tab types, but you can explore them by playing around on the DocuSign sandbox.

Every signer will have their own list of tabs. In order for DocuSign to know where to place the tabs, we're going to have to anchor them to some text in the document. This is where our function for creating standardized anchors will be important. Using the `generate_anchor` function, passing it a tab type and an email, you can generate an anchor that must BOTH be placed in your document where you want the tab to be, and set as the `'anchorString'` for the tab. It's recommended that you use something close to 11 point text in order to fit the tab nicely (signatures need two lines!), and make the text white so that it's not visible to the user.

The format for the standard anchor will look like:

```
[FIRST TEN CHARACTERS OF THE SHA1 HASH OF THE EMAIL]-[UP TO FIVE CHARACTER LONG ABBREVIATION OF THE TAG TYPE]
```

This will be unique for every type of tab you use for every recipient due to the SHA1 hash, so everything should Just Work. You can in fact use whatever system you like for the anchors, we just made this system because it's extremely simple and easy! But I won't tell you what to do, maybe your automated dice popper anchor generator is just the system for you.

As with the recipients and the documents, the tabs attached to a recipient are a list of dictionaries, each with the minimum key-value pairs:

Key | Value
--- | ---
`'type'` | Type of tab. There are LOTS of these, [here's a list](https://developers.docusign.com/esign-rest-api/reference/Envelopes/EnvelopeRecipientTabs/).
`'anchorString'` | String in document to anchor tab to

There's a LOT more to tabs, such as being able to lock ones that are normally editable, and offsetting the anchor. [Read all about that here if you're interested!](https://developers.docusign.com/esign-rest-api/guides/concepts/tabs) It can all be added into your dictionaries.

## Dependencies

You'll need pip to install:

* requests (for sending HTTP requests)
* pyjwt (for authenticating)

Hope this helps for whatever you're working on! Now if you happen to have the key to let me out of this documentation dungeon...

IF YOU'RE READING THIS IT MEANS I NEED TO SET UP LOGGING FOR REDIS, BUT THAT ALSO MEANS JASON NEEDS TO HELP, SO LIKE, HI JASON! ALSO HELP WITH DOCUMENT PASSING, LIKE, HOW ARE DOCUMENTS EVEN REPRESENTED IN DOCASSEMBLE? IF IT'S JUST A PATH TO A FILE THEN THAT'S COOL, BUT I'M ASSUMING IT'S KINDA MORE COMPLICATED