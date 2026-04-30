## 1. Service — tickets.py

- [x] 1.1 In `service/src/service/api/tickets.py`, add `HEAVY_MODEL` to the import from `service.llm.client`
- [x] 1.2 Replace `model=DEFAULT_MODEL` with `model=HEAVY_MODEL` in the `client.messages.create` call
- [x] 1.3 Replace `"model": DEFAULT_MODEL` with `"model": HEAVY_MODEL` in the `log.info` extra dict
- [x] 1.4 Remove `DEFAULT_MODEL` from the import if it is no longer used elsewhere in the file

## 2. Verification

- [x] 2.1 Run the service test suite (`pytest tests/test_tickets.py`) and confirm all tests pass
- [x] 2.2 Confirm no other test files reference `DEFAULT_MODEL` being used for scan (grep check)
