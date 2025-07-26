# app.py - improved version with better validation and error handling
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
import os
import asyncio
import random
import logging
import json
import traceback
import aiohttp
import sys
from datetime import datetime
from livekit import api as lkapi

# Setup more detailed logging
logging.basicConfig(
    level=logging.INFO if os.getenv("NODE_ENV") == "production" else logging.DEBUG, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Get LiveKit credentials from environment variables
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
AGENT_NAME = "LisstIn"


@app.route('/')
def health_check():
    """Health check endpoint for cloud providers"""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

@app.route('/index')
def index():
    return render_template("index.html")

@app.route('/submit', methods=['POST'])
def submit():
    try:
        # Get phone number from form data or JSON
        if request.is_json:
            data = request.get_json()
            name = data.get("name", " ").strip()
            phone = data.get('phone', '').strip()
        else:
            name= request.form.get("name", " ").strip()
            phone = request.form.get('phone', '').strip()
   
        # Validate required fields
        if not phone:
            return jsonify({
                "success": False,
                "message": "Phone number is required."
            }), 400
        
        logger.info(f"Processing call request for phone: {phone}")
            
        # Create random room name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = ''.join(str(random.randint(0, 9)) for _ in range(6))
        room_name = f"outbound-{timestamp}-{random_suffix}"
          
        # Prepare metadata as a JSON string
        metadata_dict = {
            "name":name,
            "phone_number": phone,
            "timestamp": timestamp,
            "call_type": "outbound"
        }
        metadata = json.dumps(metadata_dict)
        logger.info(f"Prepared metadata: {metadata}")
        
        # Create the dispatch
        logger.info(f"Creating dispatch for {phone} in room {room_name}")
        
        try:
            # Handle asyncio properly
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're in an async context, we need to run in a thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, create_dispatch(room_name, metadata))
                        result = future.result(timeout=30)  # 30 second timeout
                else:
                    result = loop.run_until_complete(create_dispatch(room_name, metadata))
            except RuntimeError:
                # No event loop exists, create a new one
                result = asyncio.run(create_dispatch(room_name, metadata))

            return jsonify({
                "success": True, 
                "message": "Your call has been scheduled. Our agent will call you shortly.",
                "details": {
                    "room_name": room_name,
                    "dispatch_id": result.get("dispatch_id", "No dispatch ID returned"),
                    "phone_number": phone
                }
            })
            
        except asyncio.TimeoutError:
            logger.error("Dispatch creation timed out")
            return jsonify({
                "success": False,
                "message": "Request timed out. Please try again."
            }), 504
            
        except Exception as inner_e:
            logger.error(f"Error in async dispatch: {str(inner_e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                "success": False,
                "message": f"Error creating dispatch: {str(inner_e)}"
            }), 500
            
    except Exception as e:
        logger.error(f"Error in form processing: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Error processing your request: {str(e)}"
        }), 500

async def create_dispatch(room_name, metadata):
    """Create a LiveKit agent dispatch"""
    session = None
    try:
        logger.debug("Creating aiohttp session")
        session = aiohttp.ClientSession()
        
        logger.debug("Creating LiveKit API client")
        lk_client = lkapi.LiveKitAPI(
            url=LIVEKIT_URL,
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET,
        )
        
        # Create dispatch request
        logger.debug(f"Creating dispatch request for agent {AGENT_NAME}")
        dispatch_request = lkapi.CreateAgentDispatchRequest(
            agent_name=AGENT_NAME,
            room=room_name,
            metadata=metadata
        )

        # Send dispatch request
        logger.info("Sending dispatch request to LiveKit")
        response = await lk_client.agent_dispatch.create_dispatch(dispatch_request)
        
        # Log the full response for debugging
        logger.debug(f"Raw dispatch response: {response}")
        
        # Extract dispatch_id safely
        dispatch_id = getattr(response, 'dispatch_id', None) or getattr(response, 'id', 'Unknown')
        
        logger.info(f"Dispatch created successfully with ID: {dispatch_id}")
        
        return {
            "dispatch_id": dispatch_id,
            "status": "success",
            "room_name": room_name
        }
        
    except Exception as e:
        logger.error(f"LiveKit dispatch error: {str(e)}")
        logger.error(traceback.format_exc())
        raise
        
    finally:
        # Explicitly close the session
        if session and not session.closed:
            await session.close()
            logger.debug("Closed aiohttp session")



if __name__ == '__main__':
    # Validate required environment variables on startup
    required_vars = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "AGENT_NAME"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    # Get port from environment variable (required for many cloud platforms)
    port = int(os.environ.get("PORT", 8999))
    
    # Print out some startup info
    logger.info(f"Starting app with LIVEKIT_URL: {LIVEKIT_URL}")
    logger.info(f"Agent name: {AGENT_NAME}")
    logger.info(f"Server starting on port: {port}")
    
    app.run(host='0.0.0.0', port=port, debug=False)