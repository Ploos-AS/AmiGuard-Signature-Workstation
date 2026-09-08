# M6.1 — Analyst queue and sample state machine

M6.1 provides a small local queue record for each imported ASW sample. It contains identifiers, state and workflow history only; malware bytes never enter queue records or Git.

## States

`imported -> static-analysis -> runtime-analysis -> candidate -> qualification -> reviewed -> closed`

Runtime analysis is optional when static evidence is sufficient, so `static-analysis -> candidate` is permitted. `rejected` is an explicit terminal path from active analysis states. `closed` is terminal. A reviewed item may return to `qualification` if review finds that qualification evidence must be revised.

The queue is workflow coordination, not a trust oracle. Moving a record to `candidate`, `qualification`, or `reviewed` does not itself satisfy M4/M5 gates.

## Usage

```sh
python3 tools/asw_queue.py new asw-123 <sha256> --queue /var/lib/asw/queue
python3 tools/asw_queue.py transition /var/lib/asw/queue/asw-123.json static-analysis --note 'static evidence started'
python3 tools/asw_queue.py show /var/lib/asw/queue/asw-123.json
```

Records are created mode 0600 with exclusive creation to prevent accidental overwrite. Existing records reject symlinks. Every transition appends an event with UTC timestamp, previous state, new state and optional analyst note.

## Safety

- Queue filenames derive only from validated ASW sample IDs.
- SHA-256 is mandatory and lowercase hexadecimal.
- No original submitter filename or private submitter data is required.
- No sample content is stored in queue JSON.
- No state transition executes, extracts, mounts or opens a sample.
- Queue storage belongs outside the Git checkout.

M6.2 will strengthen operational history into a separate append-only audit trail.
