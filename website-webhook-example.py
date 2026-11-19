"""Place this server-to-server logic in your website backend, not in public JavaScript."""
import os, json, urllib.request, uuid

def submit_inquiry(inquiry, unique_submission_id):
    payload=dict(inquiry,event_id=unique_submission_id)
    req=urllib.request.Request(os.environ['CRM_URL'].rstrip('/')+'/webhooks/leads',data=json.dumps(payload).encode(),method='POST',headers={'Content-Type':'application/json','Authorization':'Bearer '+os.environ['CRM_INGEST_TOKEN']})
    with urllib.request.urlopen(req,timeout=15) as r:return json.load(r)
# Use the same stable submission ID for every retry; map captured attribution without guessing.
