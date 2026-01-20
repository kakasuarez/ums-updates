from dataclasses import dataclass, asdict


@dataclass
class ChatOptions:
    interval: int = 600
    first: int = 2


def job_name(chat_id: int) -> str:
    return f"notices:{chat_id}"


def get_chat_options(chat_data: dict) -> ChatOptions:
    raw = chat_data.get("options")
    if isinstance(raw, dict):
        try:
            return ChatOptions(**raw)
        except:
            pass
    return ChatOptions()


def set_chat_options(chat_data: dict, options: ChatOptions) -> None:
    chat_data["options"] = asdict(options)


def get_new_chat_options() -> dict:
    return asdict(ChatOptions())
