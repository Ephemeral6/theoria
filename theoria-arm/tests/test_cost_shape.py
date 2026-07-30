"""The shape of the cost block in an archived manifest is this arm's decision.

`armtools/archive.py::costs()` used to embed `proxy.cost.price_run()`'s return
dict verbatim under `cost.from_price_table`. `proxy/` belongs to another
territory and the shape of that dict was never a declared contract, so the
coupling had a measured consequence: master commit `71b882c8` added three keys
to it, and every archived manifest that re-derives through `backfill.build()`
changed its bytes -- 7 of 7 -- turning `verify_provenance` check 8 red for the
whole `theoria-arm` territory fourteen hours after the branch it blocked was
written. The author of that commit saw it coming and said so in the message
("Known downstream consequence, reported not fixed"); nothing in this arm was
listening.

These tests are the listener. Two different things are pinned, and the second
matters more than the first:

1. **that the projection projects** -- an undeclared key is dropped, a declared
   one survives, an absent one is not invented;
2. **which fields are declared** -- specifically that the three "the total is a
   lower bound, here is why" channels are among them. Freezing the tuple at the
   five keys the pre-S29 manifests carry would have made the gate green without
   touching a single archived file, and would have been the wrong fix: it would
   have left this arm's own archive unable to say that a bill it reports is
   short, while `figures/fig02_bill_shape.py:503` prints that number as "table
   recomputes ...".
"""

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from armtools.archive import (ARCHIVE_COST_FIELDS,     # noqa: E402
                              _declared_cost, costs)
from proxy.cost import DEFAULT_TABLE, PriceTable, price_run   # noqa: E402


#: Written out again, by hand, on purpose. `ARCHIVE_COST_FIELDS` is the code
#: under test; a test that imports it and compares it to itself asserts only
#: that the code equals itself, and would stay green while somebody quietly
#: shrank the tuple back to the five pre-S29 keys to make check 8 pass. This
#: duplication is the whole mechanism: shrinking the declaration now turns this
#: file red, and going green again means editing this list, which means saying
#: out loud that the archive no longer records that channel.
EXPECTED_FIELDS = (
    "model_calls",
    "per_model",
    "pricing",
    "unpriced_models",
    "usd_total",
    # S29 / `71b882c8`. `usd_total` is a lower bound; these three are the only
    # channels that say why it is short, and they are three and not one because
    # an unmeasured call is not an unpriced model and neither is a counted key
    # the table has no rate for.
    "missing_usage_keys",
    "unmeasured_calls",
    "unpriced_usage_keys",
)

#: A fully measured call: both halves of the bill present.
MEASURED = {"input_tokens": 1000, "output_tokens": 2000}

#: The same call with the output side missing -- what an SSE stream truncated
#: before `message_delta` actually looks like. `proxy.cost` refuses to price it.
TRUNCATED = {"input_tokens": 1000}


def _table():
    return PriceTable.load(DEFAULT_TABLE)


def _call(usage, model="claude-opus-5"):
    return {"event": "model_call", "model": model, "usage": usage,
            "response": {"total_cost_usd": 0.0}}


# --------------------------------------------------- 1. the declaration itself
def test_the_declared_fields_are_pinned_by_hand_in_this_file():
    """See EXPECTED_FIELDS. The duplication is deliberate."""
    assert tuple(ARCHIVE_COST_FIELDS) == EXPECTED_FIELDS


def test_the_declaration_covers_everything_the_conversion_reports():
    """The cross-territory check: if `proxy/cost.py` grows a key, this fails.

    That is the point of failing here. The alternative -- which is what
    happened -- is that the new key silently changes the bytes of every
    archived manifest and the *merge queue* reports it, half a day later, as a
    red gate on somebody's unrelated branch.

    Fixing this failure is a judgement, not a chore: either the new field is
    something the archive should record (add it to `ARCHIVE_COST_FIELDS` and
    migrate the manifests already on disk, in the open) or it is not (say why
    in `ARCHIVE_COST_FIELDS`' comment and add it to the ignore list below).
    Neither branch is silent.
    """
    reported = set(price_run([_call(MEASURED)], _table()))
    undeclared = reported - set(ARCHIVE_COST_FIELDS)
    assert not undeclared, (
        "proxy.cost.price_run() now reports %r, which this archive does not "
        "declare. Decide whether the manifest records it, then update "
        "ARCHIVE_COST_FIELDS and EXPECTED_FIELDS together." % sorted(undeclared))


def test_the_declaration_does_not_name_fields_that_do_not_exist():
    """The other direction, and it is not symmetric with the one above.

    A declared key the conversion never returns would sit in the tuple looking
    like a recorded channel while every manifest silently omitted it -- an
    absence that reads as "nothing to report" instead of "never asked".
    """
    reported = set(price_run([_call(MEASURED)], _table()))
    phantom = set(ARCHIVE_COST_FIELDS) - reported
    assert not phantom, (
        "ARCHIVE_COST_FIELDS names %r, which price_run() does not return"
        % sorted(phantom))


# ------------------------------------------------- 2. the projection projects
def test_an_undeclared_key_is_dropped():
    """The negative control. Without this, `_declared_cost = lambda d: d` --
    the verbatim embed this whole change exists to remove -- passes every other
    test in this file."""
    out = _declared_cost({"usd_total": 1.0, "a_key_from_a_future_refactor": 7})
    assert "a_key_from_a_future_refactor" not in out
    assert out["usd_total"] == 1.0


def test_every_declared_key_survives_the_projection():
    """The positive control, and it is load-bearing: without it a
    `_declared_cost` that returned `{}` would satisfy the test above."""
    raw = {key: "sentinel-%s" % key for key in ARCHIVE_COST_FIELDS}
    out = _declared_cost(raw)
    assert out == raw


def test_a_key_the_conversion_did_not_return_is_not_invented():
    """Absent stays absent. Filling it with `None` would assert "the conversion
    considered this and found nothing", which is exactly the confusion S29
    removed one layer down: an absence encoded as a confident value."""
    out = _declared_cost({"usd_total": 1.0})
    assert set(out) == {"usd_total"}
    assert "unmeasured_calls" not in out


def test_the_failure_dict_is_passed_through_whole():
    """`costs()` puts `{"error": ...}` here when the price table cannot be
    loaded at all. It holds none of the declared fields, so projecting it would
    leave `{}` -- an empty cost block that reads like a priced run of zero
    rather than a conversion that never ran."""
    err = {"error": "ImportError: no module named proxy.cost"}
    assert _declared_cost(err) == err


# ------------------------------- 3. what the archive can still say about a bill
def test_the_manifest_can_still_say_that_its_total_is_short():
    """The test that would have caught the wrong fix.

    `usd_total` is a sum over the calls that *could* be priced
    (`proxy/cost.py:186`). A run whose stream was truncated bills real money and
    reports a total that omits it. If the archive drops `unmeasured_calls` and
    `missing_usage_keys` -- which is precisely what freezing the declaration at
    the five pre-S29 keys would do -- then the manifest, and every figure built
    from it, presents that floor as the bill with nothing anywhere saying
    otherwise.
    """
    report = costs([_call(TRUNCATED)])
    block = report["from_price_table"]

    assert block["unmeasured_calls"] == 1
    assert block["missing_usage_keys"] == ["output_tokens"]
    # ... and the floor really is short: the unmeasured call contributed nothing.
    assert block["usd_total"] == 0.0
    assert block["model_calls"] == 0


def test_a_measured_zero_is_still_reported_as_a_price():
    """The other half of the S29 distinction, kept alive at this layer.

    A call measured at zero tokens is priced -- 0.0 -- and is *not* an
    unmeasured call. If this arm ever collapses the two again, the archive
    stops being able to tell "we did not look" from "we looked and it was
    nothing", and a reader cannot recover the difference from the manifest.
    """
    report = costs([_call({"input_tokens": 0, "output_tokens": 0})])
    block = report["from_price_table"]

    assert block["unmeasured_calls"] == 0
    assert block["missing_usage_keys"] is None
    assert block["usd_total"] == 0.0
    assert block["model_calls"] == 1


def test_one_of_the_three_adopted_keys_is_redundant_and_which_one():
    """Pinned because the honest version of the claim is more useful than the
    tidy one.

    `unpriced_usage_keys` is *not* new information: it equals the
    `usage_keys_the_table_cannot_price` that `costs()` already computes itself by
    calling `table.cost()` a second time. `unmeasured_calls` and
    `missing_usage_keys` have no such sibling. So if a future reader trims the
    declaration, this test tells them which key they can drop without losing
    anything and which two they cannot -- rather than leaving them with a comment
    asserting all three are load-bearing, which is false.
    """
    report = costs([_call({"input_tokens": 100, "output_tokens": 200,
                           "mystery_tokens": 7})])

    assert report["from_price_table"]["unpriced_usage_keys"] == ["mystery_tokens"]
    assert report["usage_keys_the_table_cannot_price"] == ["mystery_tokens"]
    assert (report["from_price_table"]["unpriced_usage_keys"]
            == report["usage_keys_the_table_cannot_price"])

    # ...and the two that have no sibling really have none.
    assert "unmeasured_calls" not in report
    assert "missing_usage_keys" not in report


def test_a_priced_call_reaches_the_manifest_as_a_number():
    """Positive control for the two tests above: they both assert on runs whose
    total is 0.0, so a `costs()` that always reported zero would satisfy them."""
    report = costs([_call(MEASURED)])
    block = report["from_price_table"]

    assert block["usd_total"] > 0.0
    assert block["model_calls"] == 1
    assert block["unmeasured_calls"] == 0
    assert block["unpriced_models"] is None
