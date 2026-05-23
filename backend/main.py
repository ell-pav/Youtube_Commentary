from fastapi import FastAPI
from pydantic import BaseModel

from backend.services.agent_service import (
    generate_valid_comment
)

from backend.services.transcript_service import (
    get_video_transcript
)

from backend.services.nlp_service import (
    summarize_text
)
from backend.services.rag_service import (
    build_rag_index,
    retrieve_relevant_context
)
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm
)

from fastapi import Depends

from jose import jwt, JWTError

from backend.services.auth_service import (
    authenticate_user,
    create_access_token,
    SECRET_KEY,
    ALGORITHM
)

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login"
)

class VideoRequest(BaseModel):

    url: str

    sentiment: str


@app.get("/")
def root():

    return {
        "message": "API running. More info at /docs"
    }


@app.post("/analyze")
def analyze_video(
    data: VideoRequest,
    token: str = Depends(oauth2_scheme)
):

    video_id = data.url.split("v=")[-1]

    try:

        transcript = get_video_transcript(video_id)
        index = build_rag_index(transcript)

        context = retrieve_relevant_context(
        index,
        "main topic of the video"
)
       
    except Exception as e:

        return {
            "error": str(e)
        }

    summary = summarize_text(
        context
    )

    agent_result = generate_valid_comment(
        summary,
        data.sentiment
    )

    generated_comment = agent_result[
        "comment"
    ]

    return {

        "summary": summary,

        "generated_comment": generated_comment,

        "validated": agent_result[
            "validated"
        ],

        "attempts": agent_result[
            "attempts"
        ]
    }

@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends()
):

    authenticated = authenticate_user(
        form_data.username,
        form_data.password
    )

    if not authenticated:

        return {
            "error": "Invalid credentials"
        }

    access_token = create_access_token(
        data={
            "sub": form_data.username
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }