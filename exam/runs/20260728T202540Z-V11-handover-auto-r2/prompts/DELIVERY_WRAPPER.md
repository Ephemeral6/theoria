# The wrapper message each reader actually received

This is the text of the message that spawned each examinee, verbatim, with
`<PATH>` standing for that reader's own copy of the tier prompt. It was
identical for all six readers apart from that path.

It is written down here because the adversarial review of this run pointed out
that the blinding tests run against `tier1_manual.prompt.md` and
`tier2_manual_playbook.prompt.md`, while what a reader received was *this*
message plus one of those files. The tested artifact must be the delivered
artifact, and it was not.

`<PATH>` was
`…\scratchpad\v11-delivery-r2-4b71\{A1,A2,A3,B1,B2,B3}\TASK.md`, one directory
per reader, each containing that one file and nothing else. `A*` received
`tier1_manual.prompt.md`; `B*` received `tier2_manual_playbook.prompt.md`.
The directory letters are an arm label and should not have been in a path a
reader could see; see BLINDING.md, CORRECTION 1.

---

Read the file <PATH> and do exactly what it says.

That file is your entire task and your entire context. Do not read, search, list
or execute anything else: not the directory that file sits in, not any other
file, not any command, not the internet. Reading that one file is the only tool
use that is permitted, and any other tool use must be reported honestly in the
TOOLS: line the task asks for.

Your final message must be the JSON object the task asks for, followed by the
single TOOLS: line, and nothing else.
