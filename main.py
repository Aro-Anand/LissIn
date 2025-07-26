from dotenv import load_dotenv
import json
from livekit import agents
from livekit import api
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import google
from src.prompts.prompts import PROMPTS
from src.greetings.greeting import create_greeting, get_time_based_greeting
load_dotenv()
import os

api_key = os.getenv("GEMINI_API_KEY")
SIP_TRUNK_ID = os.getenv("SIP_TRUNK_ID")
class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=PROMPTS)


async def entrypoint(ctx: agents.JobContext):
    
    dial_info = json.loads(ctx.job.metadata)
    name = dial_info["name"]
    phone_number = dial_info["phone_number"]

    sip_participant_identity = phone_number

    if name and phone_number is not None:
        # The outbound call will be placed after this method is executed.

        try:
            await ctx.api.sip.create_sip_participant(api.CreateSIPParticipantRequest(

                ## This ensures the participant joins the correct room
                room_name=ctx.room.name,


                ## Outbound TrunkID
                sip_trunk_id=SIP_TRUNK_ID,
                sip_call_to=phone_number,
                participant_identity=sip_participant_identity,

                ## Wait untill aswered
                wait_until_answered=True,
            ))

            print("Call Picked up sucessfully!")
    
        except api.TwirpError as e:
            print(f"Error creating SIP particpant: {e.message}, "
                  f"SIP Status: {e.metadata.get('sip_status_code')} "
                  f"{e.metadata.get('sip_status')}")



    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            api_key=api_key,
            model="gemini-live-2.5-flash-preview",
            # model="gemini-2.5-flash-preview-native-audio-dialog"
            # model="gemini-2.5-flash-exp-native-audio-thinking-dialog"
            # model="gemini-2.0-flash-live-001"
            voice="Fenrir",
            temperature=0.7,
        )
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
    )

    get_time = get_time_based_greeting()
    greet = create_greeting(dial_info.get("name", "customer"),get_time, dial_info.get("query", " "))
    # await session.generate_reply(instructions=f"Your are the helpful assistant and say {greet}")
    await session.generate_reply(
        instructions=f"Greet the user and offer your assistance. And say '{greet}'"
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint, agent_name="LisstIn"))