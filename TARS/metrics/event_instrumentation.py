from pydantic import BaseModel
from datetime import datetime
from typing import Literal

class IncomingUserEvent(BaseModel):
    user_id: str
    user_name: str
    event_time: datetime
    user_agent: Literal["Slack", "GitHub", "API", "curl"]
    capability_invoked: Literal["TARS"] = "TARS"
    response_satisfaction: Literal["thumbs_up", "thumbs_down", "none"] = "none"
