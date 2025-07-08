from langchain_community.chat_message_histories import ChatMessageHistory

# cache ChatMessageHistory instances by session_id
# if we have user id combination, then we should update the code here to consider that
_session_histories = {}

def get_session_history(user_id: str, session_id: str):
    if (user_id,session_id) not in _session_histories:
        _session_histories[(user_id, session_id)] = ChatMessageHistory()
    return _session_histories[(user_id,session_id)]
