#!/usr/bin/env python3
"""
Generate dummy data for Phase 2: constituencies, candidates, and candidate-level messaging.
This allows testing the Phase 2 API functionality with realistic dummy data.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random
from faker import Faker

# API configuration
API_BASE_URL = "http://localhost:8000"
API_ENDPOINTS = {
    "messages_single": f"{API_BASE_URL}/api/v1/messages/single",
    "messages_bulk": f"{API_BASE_URL}/api/v1/messages/bulk"
}

fake = Faker('en_GB')

# UK Constituency data (sample from different regions and types)
UK_CONSTITUENCIES = [
    {"name": "Birmingham Edgbaston", "region": "West Midlands", "constituency_type": "county"},
    {"name": "Manchester Central", "region": "North West", "constituency_type": "county"},
    {"name": "Newcastle upon Tyne Central", "region": "North East", "constituency_type": "county"},
    {"name": "Leeds North East", "region": "Yorkshire and The Humber", "constituency_type": "county"},
    {"name": "Sheffield Hallam", "region": "Yorkshire and The Humber", "constituency_type": "county"},
    {"name": "Bristol West", "region": "South West", "constituency_type": "county"},
    {"name": "Brighton Pavilion", "region": "South East", "constituency_type": "county"},
    {"name": "Cambridge", "region": "East of England", "constituency_type": "county"},
    {"name": "Oxford East", "region": "South East", "constituency_type": "county"},
    {"name": "Canterbury", "region": "South East", "constituency_type": "county"},
    {"name": "Warwick and Leamington", "region": "West Midlands", "constituency_type": "county"},
    {"name": "Bath", "region": "South West", "constituency_type": "county"},
    {"name": "Richmond Park", "region": "London", "constituency_type": "district"},
    {"name": "Putney", "region": "London", "constituency_type": "district"},
    {"name": "Cities of London and Westminster", "region": "London", "constituency_type": "district"},
    {"name": "Kensington", "region": "London", "constituency_type": "district"},
    {"name": "Hackney North and Stoke Newington", "region": "London", "constituency_type": "district"},
    {"name": "Islington North", "region": "London", "constituency_type": "district"},
    {"name": "Hampstead and Kilburn", "region": "London", "constituency_type": "district"},
    {"name": "Chingford and Woodford Green", "region": "London", "constituency_type": "district"},
    {"name": "Cardiff Central", "region": "Wales", "constituency_type": "unitary"},
    {"name": "Swansea West", "region": "Wales", "constituency_type": "unitary"},
    {"name": "Wrexham", "region": "Wales", "constituency_type": "unitary"},
    {"name": "Edinburgh Central", "region": "Scotland", "constituency_type": "unitary"},
    {"name": "Glasgow Central", "region": "Scotland", "constituency_type": "unitary"},
    {"name": "Aberdeen North", "region": "Scotland", "constituency_type": "unitary"},
    {"name": "Dundee West", "region": "Scotland", "constituency_type": "unitary"},
    {"name": "Stirling", "region": "Scotland", "constituency_type": "unitary"},
    {"name": "Belfast South", "region": "Northern Ireland", "constituency_type": "district"},
    {"name": "North Down", "region": "Northern Ireland", "constituency_type": "district"}
]

def generate_candidate_name() -> str:
    """Generate realistic British candidate names."""
    british_first_names = [
        "James", "Robert", "John", "Michael", "David", "William", "Richard", "Thomas", "Christopher", "Daniel",
        "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen",
        "Andrew", "Mark", "Paul", "Steven", "Kenneth", "Edward", "Brian", "Ronald", "Anthony", "Kevin",
        "Helen", "Nancy", "Betty", "Dorothy", "Lisa", "Sandra", "Donna", "Carol", "Ruth", "Sharon"
    ]
    
    british_surnames = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Wilson", "Moore",
        "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Wood", "Lewis",
        "Clarke", "Walker", "Hall", "Allen", "Young", "King", "Wright", "Lopez", "Hill", "Scott",
        "Adams", "Baker", "Gonzalez", "Nelson", "Carter", "Mitchell", "Perez", "Roberts", "Turner", "Phillips"
    ]
    
    return f"{random.choice(british_first_names)} {random.choice(british_surnames)}"

def generate_social_media_handle(name: str) -> Dict[str, str]:
    """Generate realistic social media handles based on candidate name."""
    # Convert name to handle format
    clean_name = name.lower().replace(" ", "").replace("'", "")
    first_name, last_name = name.split(" ", 1)
    first_initial = first_name[0].lower()
    last_name_clean = last_name.lower().replace(" ", "").replace("'", "")
    
    handle_options = [
        f"{clean_name}",
        f"{first_initial}{last_name_clean}",
        f"{clean_name}reform",
        f"{clean_name}{random.randint(1, 99)}",
        f"reform{clean_name}"
    ]
    
    twitter_handle = f"@{random.choice(handle_options)}"
    facebook_url = f"https://facebook.com/{random.choice(handle_options)}"
    
    return {
        "twitter": twitter_handle,
        "facebook": facebook_url
    }

# Reform UK political messaging themes for dummy content
REFORM_MESSAGING_THEMES = {
    "immigration": [
        "We need to control our borders and implement smart immigration policies that work for Britain.",
        "Mass immigration has put unsustainable pressure on our public services and housing.",
        "It's time to put British workers first and end the wage-suppressing effects of unlimited immigration.",
        "We will stop the small boats crisis and restore order to our immigration system.",
        "Britain needs an immigration system that serves our national interest, not global elites."
    ],
    "economy": [
        "We will cut taxes for hardworking families and small businesses across the constituency.",
        "British workers deserve better - we'll raise the tax threshold to £20,000.",
        "Our economy is being held back by excessive regulation and high taxes.",
        "We need to unleash British enterprise and support our local businesses.",
        "It's time to end the cost-of-living crisis with real economic reform."
    ],
    "brexit": [
        "We must deliver the Brexit that people voted for - true independence from EU control.",
        "Brussels bureaucrats should not be making laws for Britain.",
        "We need to maximize the opportunities of Brexit for British businesses.",
        "The establishment tried to overturn Brexit - we won't let them.",
        "Brexit means taking back control of our laws, borders, and money."
    ],
    "net_zero": [
        "Net Zero policies are making energy unaffordable for ordinary families.",
        "We should be using Britain's natural gas reserves to bring down energy bills.",
        "Green ideology is destroying British jobs and making us poorer.",
        "Families shouldn't have to choose between heating and eating.",
        "Common sense energy policy means affordable bills for everyone."
    ],
    "local_issues": [
        "Our local high street needs support - we'll cut business rates for small shops.",
        "Potholes and poor road maintenance are a disgrace - we need better local investment.",
        "Our community deserves better public transport links and infrastructure.",
        "Local schools and hospitals are under pressure - we need proper funding.",
        "Planning decisions should be made locally, not by distant bureaucrats."
    ],
    "law_and_order": [
        "We need more police on our streets and zero tolerance for crime.",
        "Anti-social behaviour is making life miserable for law-abiding residents.",
        "Criminals must face proper consequences - not soft sentences.",
        "Our communities deserve to feel safe day and night.",
        "We'll back our police and give them the powers they need."
    ]
}

def generate_candidate_message(candidate_name: str, constituency_name: str, theme: str) -> str:
    """Generate realistic candidate messaging content."""
    base_messages = REFORM_MESSAGING_THEMES[theme]
    base_message = random.choice(base_messages)
    
    # Add local/personal touch
    personal_touches = [
        f"Here in {constituency_name}, {base_message.lower()}",
        f"As your Reform UK candidate for {constituency_name}, I believe {base_message.lower()}",
        f"The people of {constituency_name} deserve better. {base_message}",
        f"I'm fighting for {constituency_name} because {base_message.lower()}",
        f"Join me in making {constituency_name} a place where {base_message.lower()}"
    ]
    
    return random.choice(personal_touches)

def create_constituency_candidate_data() -> tuple[List[Dict], List[Dict]]:
    """Create constituency and candidate data."""
    constituencies = []
    candidates = []
    
    for i, constituency_info in enumerate(UK_CONSTITUENCIES):
        # Create constituency
        constituency = {
            "id": i + 1,
            "name": constituency_info["name"],
            "region": constituency_info["region"],
            "constituency_type": constituency_info["constituency_type"]
        }
        constituencies.append(constituency)
        
        # Create 1-2 candidates per constituency
        num_candidates = random.choice([1, 2])
        for j in range(num_candidates):
            candidate_name = generate_candidate_name()
            candidate = {
                "id": len(candidates) + 1,
                "name": candidate_name,
                "constituency_id": constituency["id"],
                "social_media_accounts": generate_social_media_handle(candidate_name),
                "candidate_type": "local" if j == 0 else "local"  # Could have national/both later
            }
            candidates.append(candidate)
    
    return constituencies, candidates

def create_candidate_messages(candidates: List[Dict], constituencies: List[Dict]) -> List[Dict]:
    """Create candidate-level messaging data."""
    messages = []
    constituency_lookup = {c["id"]: c["name"] for c in constituencies}
    
    for candidate in candidates:
        constituency_name = constituency_lookup[candidate["constituency_id"]]
        
        # Generate 3-8 messages per candidate
        num_messages = random.randint(3, 8)
        
        for _ in range(num_messages):
            # Pick random theme
            theme = random.choice(list(REFORM_MESSAGING_THEMES.keys()))
            
            # Generate message content
            content = generate_candidate_message(candidate["name"], constituency_name, theme)
            
            # Create message date (campaign period: March-May 2024)
            start_date = datetime(2024, 3, 1)
            end_date = datetime(2024, 5, 2)
            published_date = fake.date_time_between(start_date=start_date, end_date=end_date)
            
            # Create message data
            message = {
                "url": f"https://twitter.com/{candidate['social_media_accounts']['twitter'][1:]}/status/{random.randint(1700000000000000000, 1799999999999999999)}",
                "title": f"{candidate['name']} - {theme.replace('_', ' ').title()} Message",
                "content": content,
                "published_date": published_date.strftime("%Y-%m-%d"),
                "author": candidate["name"],
                "source_type": "twitter",
                "source_name": f"{candidate['name']} Twitter",
                "platform": "twitter",
                "candidate_id": candidate["id"],
                "geographic_scope": "local",
                "engagement_metrics": {
                    "views": random.randint(50, 5000),
                    "shares": random.randint(5, 100),
                    "likes": random.randint(10, 200),
                    "comments": random.randint(2, 50)
                },
                "raw_data": {
                    "candidate_name": candidate["name"],
                    "constituency": constituency_name,
                    "theme": theme,
                    "message_type": "candidate_tweet"
                },
                "keywords": [theme.replace('_', ' '), constituency_name.split()[0].lower(), "reform uk", "candidate"],
                "issue_category": theme
            }
            messages.append(message)
    
    return messages

def populate_database_via_api():
    """Populate database with Phase 2 dummy data via API."""
    print("🚀 Generating Phase 2 dummy data...")
    
    # Generate data
    constituencies, candidates = create_constituency_candidate_data()
    messages = create_candidate_messages(candidates, constituencies)
    
    print(f"📊 Generated:")
    print(f"  - {len(constituencies)} constituencies")
    print(f"  - {len(candidates)} candidates")  
    print(f"  - {len(messages)} candidate messages")
    
    # For now, we'll create a simple data insertion script since the API might not have
    # constituency/candidate endpoints yet. Let's create the data and save it for manual insertion.
    
    # Save data to files for inspection
    with open('dummy_constituencies.json', 'w') as f:
        json.dump(constituencies, f, indent=2)
    
    with open('dummy_candidates.json', 'w') as f:
        json.dump(candidates, f, indent=2)
    
    with open('dummy_candidate_messages.json', 'w') as f:
        json.dump(messages[:10], f, indent=2)  # Sample for inspection
    
    print(f"\n📁 Saved sample data files:")
    print(f"  - dummy_constituencies.json ({len(constituencies)} items)")
    print(f"  - dummy_candidates.json ({len(candidates)} items)")
    print(f"  - dummy_candidate_messages.json (sample of {min(10, len(messages))} items)")
    
    return constituencies, candidates, messages

def insert_data_directly():
    """Insert data directly into database (bypassing API for now)."""
    from src.database import get_session
    from src.models import Constituency, Candidate, Source, Message, Keyword
    
    constituencies, candidates, messages = populate_database_via_api()
    
    print(f"\n💾 Inserting data into database...")
    
    with next(get_session()) as db:
        # Insert constituencies
        db_constituencies = []
        for const_data in constituencies:
            constituency = Constituency(
                name=const_data["name"],
                region=const_data["region"],
                constituency_type=const_data["constituency_type"]
            )
            db.add(constituency)
            db_constituencies.append(constituency)
        
        db.commit()
        
        # Insert candidates
        db_candidates = []
        for cand_data in candidates:
            candidate = Candidate(
                name=cand_data["name"],
                constituency_id=cand_data["constituency_id"],
                social_media_accounts=cand_data["social_media_accounts"],
                candidate_type=cand_data["candidate_type"]
            )
            db.add(candidate)
            db_candidates.append(candidate)
        
        db.commit()
        
        # Create sources for candidates
        sources_created = {}
        for cand_data in candidates:
            source_name = f"{cand_data['name']} Twitter"
            if source_name not in sources_created:
                source = Source(
                    name=source_name,
                    url=f"https://twitter.com/{cand_data['social_media_accounts']['twitter'][1:]}",
                    source_type="twitter",
                    active=True
                )
                db.add(source)
                db.commit()
                sources_created[source_name] = source.id
        
        # Insert messages
        for msg_data in messages:
            # Find the source
            source_name = msg_data["source_name"]
            source_id = sources_created.get(source_name)
            
            if source_id:
                message = Message(
                    source_id=source_id,
                    candidate_id=msg_data["candidate_id"],
                    content=msg_data["content"],
                    url=msg_data["url"],
                    published_at=datetime.strptime(msg_data["published_date"], "%Y-%m-%d"),
                    message_type="post",
                    geographic_scope=msg_data["geographic_scope"],
                    message_metadata=msg_data["engagement_metrics"],
                    raw_data=msg_data["raw_data"]
                )
                db.add(message)
                db.commit()
                
                # Add keywords
                for keyword_text in msg_data["keywords"]:
                    keyword = Keyword(
                        message_id=message.id,
                        keyword=keyword_text,
                        confidence=1.0,
                        extraction_method="dummy_generator"
                    )
                    db.add(keyword)
        
        db.commit()
        
        print(f"✅ Successfully inserted all Phase 2 dummy data!")
        print(f"  - {len(constituencies)} constituencies")
        print(f"  - {len(candidates)} candidates")
        print(f"  - {len(messages)} messages")
        print(f"  - {len(messages) * len(messages[0]['keywords'])} keywords (approx)")

def main():
    """Main function."""
    print("🎯 Phase 2 Dummy Data Generator")
    print("=" * 50)
    
    try:
        insert_data_directly()
        print(f"\n🎉 Phase 2 dummy data generation complete!")
        print(f"You can now test the Phase 2 API endpoints and dashboard.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())