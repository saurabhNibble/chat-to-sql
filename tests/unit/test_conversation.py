from app.services.conversation import ConversationStore


def test_conversation_get_or_create_new():
    store = ConversationStore()
    state = store.get_or_create()
    assert state.conversation_id is not None
    assert len(state.messages) == 0


def test_conversation_get_existing():
    store = ConversationStore()
    state1 = store.get_or_create()
    state2 = store.get_or_create(state1.conversation_id)
    assert state1.conversation_id == state2.conversation_id


def test_conversation_multi_turn_clarification_resolution():
    store = ConversationStore()
    state = store.get_or_create()

    # Turn 1: user asks ambiguous query
    prompt1 = "Show top 5"
    store.record_turn(
        state,
        user_prompt=prompt1,
        assistant_response="Which table do you mean?",
        clarification_needed=True,
        clarification_question="Which table do you mean?",
        options=["customers", "orders"],
    )
    assert state.pending_prompt == "Show top 5"

    # Turn 2: user selects "customers"
    prompt2 = "customers"
    resolved_prompt = store.resolve_prompt(state, prompt2)
    assert resolved_prompt == "Show top 5 from customers"
    assert state.pending_prompt is None
