#!/usr/bin/env python3
"""
Script to generate API data from Reform UK Contract PDF content.
Extracts key messages and policy positions to submit to the API.
"""

import requests
import json
from datetime import datetime
from typing import List, Dict, Any

# API configuration
API_BASE_URL = "http://localhost:8000"
API_ENDPOINTS = {
    "messages_single": f"{API_BASE_URL}/api/v1/messages/single",
    "messages_bulk": f"{API_BASE_URL}/api/v1/messages/bulk"
}

def create_message_data(title: str, content: str, keywords: List[str], 
                       issue_category: str, url: str = None) -> Dict[str, Any]:
    """Create standardized message data for API submission."""
    return {
        "url": url or f"https://www.reformparty.uk/contract-{title.lower().replace(' ', '-').replace(':', '')}",
        "title": title,
        "content": content,
        "published_date": "2024-06-18",  # Reform UK manifesto publication date
        "author": "Reform UK",
        "source_type": "website",
        "source_name": "Reform UK Official Website",
        "platform": "website",
        "engagement_metrics": {
            "views": 0,
            "shares": 0,
            "likes": 0,
            "comments": 0
        },
        "raw_data": {
            "document_type": "political_manifesto",
            "section": title,
            "party": "Reform UK",
            "document_source": "Reform UK Contract with You"
        },
        "keywords": keywords,
        "issue_category": issue_category
    }

def generate_reform_contract_messages() -> List[Dict[str, Any]]:
    """Generate structured message data from Reform UK Contract content."""
    
    messages = []
    
    # Core Pledges
    messages.append(create_message_data(
        title="Core Pledge: Smart Immigration Not Mass Immigration",
        content="All non-essential immigration frozen to boost wages, protect public services, end the housing crisis and cut crime. Reform UK will secure Britain's borders to protect wages, our public services, and British culture and values.",
        keywords=["immigration", "wages", "public services", "housing crisis", "crime", "borders", "british culture"],
        issue_category="immigration"
    ))
    
    messages.append(create_message_data(
        title="Core Pledge: Stop Small Boats",
        content="Illegal migrants who come to the UK will be detained and deported. If needed, migrants in small boats will be picked up and taken back to France. Leave the European Convention on Human Rights.",
        keywords=["small boats", "illegal migrants", "deportation", "france", "echr", "detention"],
        issue_category="immigration"
    ))
    
    messages.append(create_message_data(
        title="Core Pledge: Zero NHS Waiting Lists",
        content="Still free at the point of delivery, healthcare needs reform to improve outcomes and enjoy zero NHS waiting lists. Cut back office waste to spend more money on the frontline. Tax breaks for doctors and nurses.",
        keywords=["nhs", "waiting lists", "healthcare", "tax breaks", "doctors", "nurses", "frontline"],
        issue_category="healthcare"
    ))
    
    messages.append(create_message_data(
        title="Core Pledge: Good Wages for Hard Work",
        content="Lift the income tax starting threshold to £20k to save the lowest paid £1,500 per year. This takes 7 million of the least well-off out of Income Tax to make work pay and get people off benefits.",
        keywords=["income tax", "wages", "benefits", "tax threshold", "work pay"],
        issue_category="economy"
    ))
    
    messages.append(create_message_data(
        title="Core Pledge: Affordable Energy Bills",
        content="Scrap energy levies and Net Zero to slash energy bills and save each household £500 per year. Unlock Britain's vast oil and gas reserves to beat the cost of living crisis and unleash real economic growth.",
        keywords=["energy bills", "net zero", "oil", "gas", "cost of living", "economic growth"],
        issue_category="energy"
    ))
    
    # Immigration Policy Details
    messages.append(create_message_data(
        title="Immigration: Employer Immigration Tax",
        content="The National Insurance rate will be raised to 20% for foreign workers. This would incentivise businesses to employ British citizens whose National Insurance rate would stay at 13.8%. This would boost wages and could raise more than £20 billion over five years.",
        keywords=["employer tax", "foreign workers", "national insurance", "british citizens", "wages"],
        issue_category="immigration"
    ))
    
    # Economic Policies
    messages.append(create_message_data(
        title="Business: Corporation Tax Cuts",
        content="Free over 1.2 million small and medium sized businesses from Corporation Tax. Lift the minimum profit threshold to £100k. Reduce the main Corporation Tax Rate from 25% to 20%, then to 15% from Year 3.",
        keywords=["corporation tax", "small business", "medium business", "tax cuts", "entrepreneurs"],
        issue_category="economy"
    ))
    
    messages.append(create_message_data(
        title="Government Waste: Save £5 in every £100",
        content="Every department must slash wasteful spending, cut bureaucracy, improve efficiency and negotiate better value procurement without touching frontline services. This will save £50 billion per year.",
        keywords=["government waste", "bureaucracy", "efficiency", "procurement", "savings"],
        issue_category="government_efficiency"
    ))
    
    # Net Zero and Energy
    messages.append(create_message_data(
        title="Energy: Scrap Net Zero",
        content="Ditching Net Zero could save the public sector over £30 billion per year for the next 25 years. Scrap Annual £10 Billion of Renewable Energy Subsidies. Start fast-track licences of North Sea gas and oil.",
        keywords=["net zero", "renewable subsidies", "north sea", "gas", "oil", "energy costs"],
        issue_category="energy"
    ))
    
    # Law and Order
    messages.append(create_message_data(
        title="Policing: Zero Tolerance",
        content="Recruitment to increase UK per capita police numbers to 300 per 100k population. That is 40,000 new front-line officers. Clampdown on all crime and antisocial behaviour. Increase Stop and Search substantially.",
        keywords=["police numbers", "zero tolerance", "crime", "antisocial behaviour", "stop and search"],
        issue_category="law_and_order"
    ))
    
    # Education
    messages.append(create_message_data(
        title="Education: Patriotic Curriculum",
        content="Any teaching about a period or example of British or European imperialism or slavery must be paired with the teaching of a non-European occurrence of the same to ensure balance. Our children must be taught about their heritage.",
        keywords=["education", "curriculum", "british heritage", "imperialism", "slavery", "balance"],
        issue_category="education"
    ))
    
    messages.append(create_message_data(
        title="Education: Ban Transgender Ideology",
        content="No gender questioning, social transitioning or pronoun swapping in schools. Inform parents of under 16s about their children's life decisions. Schools must have single sex facilities.",
        keywords=["transgender", "schools", "parents", "children", "single sex", "ideology"],
        issue_category="education"
    ))
    
    # Benefits and Welfare
    messages.append(create_message_data(
        title="Benefits: Two-Strike Rule",
        content="All job seekers and those fit to work must find employment within 4 months or accept a job after 2 offers. Otherwise, benefits are withdrawn. In Britain, if you can work, you must work.",
        keywords=["benefits", "job seekers", "employment", "work", "welfare"],
        issue_category="welfare"
    ))
    
    # Defence
    messages.append(create_message_data(
        title="Defence: Increase Military Spending",
        content="Increase Defence Spending to 2.5% of National GDP by year 3, then 3% within 6 years. Recruit 30,000 to join the army full time. Introduce urgent pay review for armed forces.",
        keywords=["defence spending", "military", "army", "nato", "armed forces", "recruitment"],
        issue_category="defence"
    ))
    
    # Brexit
    messages.append(create_message_data(
        title="Brexit: Scrap EU Regulations",
        content="Britain still has over 6,700 retained EU laws, which we will rescind. Abandon the Windsor Framework. Prepare for renegotiations on the EU Trade and Cooperation Agreement.",
        keywords=["brexit", "eu laws", "windsor framework", "trade agreement", "regulations"],
        issue_category="brexit"
    ))
    
    return messages

def submit_messages_to_api(messages: List[Dict[str, Any]], use_bulk: bool = True) -> None:
    """Submit messages to the API."""
    
    if use_bulk and len(messages) <= 100:
        # Use bulk endpoint
        try:
            response = requests.post(
                API_ENDPOINTS["messages_bulk"],
                json={"messages": messages},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            print(f"✅ Successfully submitted {len(messages)} messages via bulk endpoint")
            print(f"Response: {response.json()}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error submitting bulk messages: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response text: {e.response.text}")
    else:
        # Use single endpoint for each message
        success_count = 0
        for i, message in enumerate(messages, 1):
            try:
                response = requests.post(
                    API_ENDPOINTS["messages_single"],
                    json=message,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                success_count += 1
                print(f"✅ Message {i}/{len(messages)}: {message['title']}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Error submitting message {i}: {message['title']}")
                print(f"Error: {e}")
        
        print(f"\n📊 Summary: {success_count}/{len(messages)} messages submitted successfully")

def main():
    """Main function to generate and submit Reform UK Contract data."""
    
    print("🚀 Generating Reform UK Contract message data...")
    
    # Generate messages
    messages = generate_reform_contract_messages()
    print(f"📝 Generated {len(messages)} messages from Reform UK Contract")
    
    # Print sample message for verification
    print("\n📋 Sample message:")
    print(json.dumps(messages[0], indent=2))
    
    # Submit to API
    print(f"\n📤 Submitting {len(messages)} messages to API...")
    submit_messages_to_api(messages, use_bulk=True)

if __name__ == "__main__":
    main()