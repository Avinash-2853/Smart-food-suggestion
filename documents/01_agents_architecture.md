# Smart Food Suggestion System - Agents Architecture

This document outlines the architecture and planning for the AI Agentic System designed to suggest and order food based on user queries.

We are implementing a two-agent system to handle these responsibilities effectively:

## 1. AI Search & Suggestion Agent
The primary role of this agent is to process user requests, search the available food data, and generate curated food suggestions.

**Capabilities:**
- Takes natural language queries from the user (e.g., "I need to arrange a party for 20 vegan people").
- Searches for suitable food items across data from various restaurants.
- Intelligently combines different items from different restaurants to create a cohesive meal or party menu.
- Displays the compiled suggestions to the user for review.

## 2. Ordering Agent
Once the user is satisfied with the suggested food items, this second agent takes over to handle the logistics.

**Capabilities:**
- Receives the finalized food data/selections approved by the user.
- Processes and places the actual orders based on the user's query and selected items.

## 3. QA & Critic Agent (Menu Reviewer)
This agent acts as a quality control checkpoint before presenting suggestions to the user.

**Capabilities:**
- Reviews the Search Agent's output to ensure the suggested menu makes logical sense and fully satisfies constraints (e.g., sufficient portions for a party size, proper variety of courses/drinks).
- Provides feedback to the Search Agent to regenerate or improve the menu if it falls short of the user's prompt requriements.

## 4. Nutrition & Health Agent
This agent focuses on the health and dietary composition of the food suggestions.

**Capabilities:**
- Analyzes the `nutritional_info` available in the dataset (calories, protein, carbs, fat, fiber, sodium).
- Filters or highlights meals according to strict health goals (e.g., "high protein", "low calorie", "keto").
- Provides a nutritional summary of the entire combined order.
