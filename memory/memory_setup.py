from langchain_community.chat_message_histories import ChatMessageHistory

# cache ChatMessageHistory instances by session_id
_session_histories = {}

def get_session_history(session_id: str):
    if session_id not in _session_histories:
        _session_histories[session_id] = ChatMessageHistory()
    return _session_histories[session_id]
