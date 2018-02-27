def comment_options_extensions(s, v):
  return s.extensions(v, (
    ( "beneficiaries", lambda s2, v2: s2.array(v2, "beneficiary") ),
  ))

operation_variants = (
  (
    "vote",
    (
      ("voter", "string"),
      ("author", "string"),
      ("permlink", "string"),
      ("weight", "int16")
    )
  ),
  (
    "comment",
    (
      ("parent_author", "string"),
      ("parent_permlink", "string"),
      ("author", "string"),
      ("permlink", "string"),
      ("title", "string"),
      ("body", "string"),
      ("json_metadata", "string")
    )
  ),
  (
    "transfer",
    (("from", "string"), ("to", "string"), ("amount", "asset"), ("memo", "string"))
  ),
  (
    "transfer_to_vesting",
    (("from", "string"), ("to", "string"), ("amount", "asset"))
  ),
  ("withdraw_vesting", (("account", "string"), ("vesting_shares", "asset"))),
  (
    "limit_order_create",
    (
      ("owner", "string"),
      ("orderid", "uint32"),
      ("amount_to_sell", "asset"),
      ("min_to_receive", "asset"),
      ("fill_or_kill", "boolean"),
      ("expiration", "time_point_sec")
    )
  ),
  ("limit_order_cancel", (("owner", "string"), ("orderid", "uint32"))),
  ("feed_publish", (("publisher", "string"), ("exchange_rate", "price"))),
  (
    "convert",
    (("owner", "string"), ("requestid", "uint32"), ("amount", "asset"))
  ),
  (
    "account_create",
    (
      ("fee", "asset"),
      ("creator", "string"),
      ("new_account_name", "string"),
      ("owner", "authority"),
      ("active", "authority"),
      ("posting", "authority"),
      ("memo_key", "public_key"),
      ("json_metadata", "string")
    )
  ),
  (
    "account_update",
    (
      ("account", "string"),
      ("owner", lambda s, v: s.optional(v, "authority")),
      ("active", lambda s, v: s.optional(v, "authority")),
      ("posting", lambda s, v: s.optional(v, "authority")),
      ("memo_key", "public_key"),
      ("json_metadata", "string")
    )
  ),
  (
    "witness_update",
    (
      ("owner", "string"),
      ("url", "string"),
      ("block_signing_key", "public_key"),
      ("props", "chain_properties"),
      ("fee", "asset")
    )
  ),
  (
    "account_witness_vote",
    (("account", "string"), ("witness", "string"), ("approve", "boolean"))
  ),
  ("account_witness_proxy", (("account", "string"), ("proxy", "string"))),
  (
    "custom",
    (("required_auths", lambda s, v: s.array(v, "string")), ("id", "uint32"), ("data", "raw_bytes"))
  ),
  (
    "report_over_production",
    (
      ("reporter", "string"),
      ("first_block", "signed_block_header"),
      ("second_block", "signed_block_header")
    )
  ),
  ("delete_comment", (("author", "string"), ("permlink", "string"))),
  (
    "custom_json",
    (
      ("required_auths", lambda s, v: s.array(v, "string")),
      ("required_posting_auths", lambda s, v: s.array(v, "string")),
      ("id", "string"),
      ("json", "string")
    )
  ),
  (
    "comment_options",
    (
      ("author", "string"),
      ("permlink", "string"),
      ("max_accepted_payout", "asset"),
      ("percent_steem_dollars", "uint32"),
      ("allow_votes", "boolean"),
      ("allow_curation_rewards", "boolean"),
      ("extensions", comment_options_extensions)
    )
  ),
  (
    "set_withdraw_vesting_route",
    (
      ("from_account", "string"),
      ("to_account", "string"),
      ("percent", "uint32"),
      ("auto_vest", "boolean")
    )
  ),
  (
    "limit_order_create2",
    (
      ("owner", "string"),
      ("orderid", "uint32"),
      ("amount_to_sell", "asset"),
      ("fill_or_kill", "boolean"),
      ("exchange_rate", "price"),
      ("expiration", "time_point_sec")
    )
  ),
  (
    "challenge_authority",
    (
      ("challenger", "string"),
      ("challenged", "string"),
      ("require_owner", "boolean")
    )
  ),
  ("prove_authority", (("challenged", "string"), ("require_owner", "boolean"))),
  (
    "request_account_recovery",
    (
      ("recovery_account", "string"),
      ("account_to_recover", "string"),
      ("new_owner_authority", "authority"),
      ("extensions", lambda s, v: s.array(v, "void"))
    )
  ),
  (
    "recover_account",
    (
      ("account_to_recover", "string"),
      ("new_owner_authority", "authority"),
      ("recent_owner_authority", "authority"),
      ("extensions", lambda s, v: s.array(v, "void"))
    )
  ),
  (
    "change_recovery_account",
    (
      ("account_to_recover", "string"),
      ("new_recovery_account", "string"),
      ("extensions", lambda s, v: s.array(v, "void"))
    )
  ),
  (
    "escrow_transfer",
    (
      ("from", "string"),
      ("to", "string"),
      ("agent", "string"),
      ("escrow_id", "uint32"),
      ("sbd_amount", "asset"),
      ("steem_amount", "asset"),
      ("fee", "asset"),
      ("ratification_deadline", "time_point_sec"),
      ("escrow_expiration", "time_point_sec"),
      ("json_metadata", "string")
    )
  ),
  (
    "escrow_dispute",
    (
      ("from", "string"),
      ("to", "string"),
      ("agent", "string"),
      ("who", "string"),
      ("escrow_id", "uint32")
    )
  ),
  (
    "escrow_release",
    (
      ("from", "string"),
      ("to", "string"),
      ("agent", "string"),
      ("who", "string"),
      ("receiver", "string"),
      ("escrow_id", "uint32"),
      ("sbd_amount", "asset"),
      ("steem_amount", "asset")
    )
  ),
  (
    "escrow_approve",
    (
      ("from", "string"),
      ("to", "string"),
      ("agent", "string"),
      ("who", "string"),
      ("escrow_id", "uint32"),
      ("approve", "boolean")
    )
  ),
  (
    "transfer_to_savings",
    (("from", "string"), ("to", "string"), ("amount", "asset"), ("memo", "string"))
  ),
  (
    "transfer_from_savings",
    (
      ("from", "string"),
      ("request_id", "uint32"),
      ("to", "string"),
      ("amount", "asset"),
      ("memo", "string")
    )
  ),
  (
    "cancel_transfer_from_savings",
    (("from", "string"), ("request_id", "uint32"))
  ),
  (
    "custom_bytes",
    (
      ("required_owner_auths", lambda s, v: s.array(v, "string")),
      ("required_active_auths", lambda s, v: s.array(v, "string")),
      ("required_posting_auths", lambda s, v: s.array(v, "string")),
      ("required_auths", lambda s, v: s.array(v, "authority")),
      ("id", "string"),
      ("data", "raw_bytes")
    )
  ),
  ("decline_voting_rights", (("account", "string"), ("decline", "boolean"))),
  (
    "reset_account",
    (
      ("reset_account", "string"),
      ("account_to_reset", "string"),
      ("new_owner_authority", "authority")
    )
  ),
  (
    "set_reset_account",
    (
      ("account", "string"),
      ("current_reset_account", "string"),
      ("reset_account", "string")
    )
  ),
  (
    "claim_reward_balance",
    (
      ("account", "string"),
      ("reward_steem", "asset"),
      ("reward_sbd", "asset"),
      ("reward_vests", "asset")
    )
  ),
  (
    "delegate_vesting_shares",
    (
      ("delegator", "string"),
      ("delegatee", "string"),
      ("vesting_shares", "asset")
    )
  ),
  (
    "account_create_with_delegation",
    (
      ("fee", "asset"),
      ("delegation", "asset"),
      ("creator", "string"),
      ("new_account_name", "string"),
      ("owner", "authority"),
      ("active", "authority"),
      ("posting", "authority"),
      ("memo_key", "public_key"),
      ("json_metadata", "string"),
      ("extensions", lambda s, v: s.array(v, "void"))
    )
  )
)
