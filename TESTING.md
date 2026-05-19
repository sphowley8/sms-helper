# TESTING.md

## TODO — Tests to Implement

### Unit Tests
- [ ] `sms_parser.py` — valid command parses correctly (`notes add/todo -item1 -item2`)
- [ ] `sms_parser.py` — missing action/target separator `/` raises `ParseError`
- [ ] `sms_parser.py` — missing items (no `-` prefixed content) raises `ParseError`
- [ ] `sms_parser.py` — only function provided (too few parts) raises `ParseError`
- [ ] `sms_parser.py` — function and action/target are lowercased
- [ ] `sms_parser.py` — items with multi-word content parse correctly (`-water plants` → `"water plants"`)
- [ ] `github_client.py` — `append_notes` appends to existing file (mock HTTP)
- [ ] `github_client.py` — `append_notes` creates new file with header when 404 (mock HTTP)
- [ ] `github_client.py` — GitHub API non-404 error raises `RuntimeError`
- [ ] `handler.py` — message from unauthorized number is dropped silently
- [ ] `handler.py` — parse error sends failure SMS reply
- [ ] `handler.py` — unknown function sends failure SMS reply
- [ ] `handler.py` — GitHub error sends failure SMS reply with details
- [ ] `handler.py` — successful notes add sends "Got it, updated"

### Integration Tests
- [ ] End-to-end: invoke Lambda locally with a sample SNS event → verify GitHub commit appears in `sphowley8/sean-brain`
- [ ] End-to-end: invoke Lambda with bad command → verify error SMS is sent via Pinpoint

### Security Tests
- [ ] Verify Lambda rejects messages from any number other than `AUTHORIZED_PHONE`
- [ ] Verify `GITHUB_TOKEN` is never logged to CloudWatch
- [ ] Verify `target` filename is sanitized to prevent path traversal (e.g., `../../etc/passwd` as target)

### Performance Tests
- [ ] Lambda cold start time under 2 seconds
- [ ] End-to-end latency (text sent → reply received) under 10 seconds at p95

---

## Tests Implemented

None yet — tests to be added in a future session.

---

## Notes on Test Strategy

- Unit tests should mock `urllib.request.urlopen` and `boto3` clients rather than making real HTTP/AWS calls.
- Integration tests require real credentials (`GITHUB_TOKEN`, `PINPOINT_APP_ID`, etc.) and should be run manually or in a separate CI job with secrets access.
- Security test for path traversal: `target` should be validated to be alphanumeric + hyphens only before constructing the GitHub file path.
