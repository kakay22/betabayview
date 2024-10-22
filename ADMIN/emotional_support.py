from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import random
import re

# Expanded responses for emotional and specific issue support
EMOTIONAL_RESPONSES = {
    'positive': [
        "I'm glad to hear you're feeling good! Is there anything else you'd like to talk about?",
        "That's awesome! What’s been making you feel so great lately?",
        "It sounds like you’re in a great mood! Any exciting plans or something fun you’re looking forward to?",
        "I'm so happy to hear things are going well for you! If there's anything on your mind, feel free to share.",
        "It’s wonderful that you're feeling positive! What’s something that’s made you smile today?",
        "You sound really upbeat! Want to talk about what’s going right in your life right now?",
        "That's fantastic! I love hearing good news. Anything else you'd like to chat about?"
    ],
    'neutral': [
        "I see you're feeling okay. Anything you'd like to talk about today?",
        "It sounds like you're feeling steady. Anything on your mind you'd like to discuss?",
        "It seems like you're in a balanced state today. I'm here if there's anything you want to chat about.",
        "You seem to be doing alright. Is there something you'd like to explore or talk about?",
        "It's good to hear you're doing okay. If there’s anything that’s been on your mind, feel free to share."
    ],
    'negative': [
        "I'm really sorry you're feeling this way. Do you want to talk about it?",
        "It sounds like things are tough right now. I'm here for you. Would you like to share more?",
        "I'm sorry you're feeling down. Sometimes talking about it helps—I'm here to listen.",
        "I’m really sorry you’re going through this. Is there anything I can do to help or just listen?",
        "It seems like you’ve been having a rough time. I'm here for you, and we can talk about anything that's on your mind.",
        "It must be really hard for you right now. Do you want to tell me more about what’s going on?",
        "I'm sorry you're feeling this way. It's okay to feel down sometimes. I'm here if you need to talk."
    ],
    'frustrated': [
        "It sounds like you’re feeling frustrated. What’s been bothering you lately?",
        "I can sense your frustration. Want to talk through it and maybe find a way to ease some of the tension?",
        "It seems like you're upset. Do you want to share what's been getting to you?",
        "Frustration can really weigh you down. I’m here to listen if you want to vent or discuss what’s been going on.",
        "I'm sorry things are feeling so frustrating right now. Maybe we can explore what's causing this and figure out a plan?"
    ],
    'overwhelmed': [
        "I can tell you're feeling overwhelmed. It's okay to take things one step at a time. Do you want to talk through what's on your plate?",
        "It sounds like everything is piling up. Sometimes just sharing what's stressing you out helps a lot. I'm here if you want to talk.",
        "I'm sorry you're feeling so overwhelmed. Is there a specific area where things are getting out of hand? We can explore ways to manage it.",
        "Feeling overwhelmed can be exhausting. Let’s break things down—what’s the main thing that’s weighing you down right now?",
        "It seems like there’s a lot going on. Let’s start small—what’s one thing you want to talk through or manage right now?"
    ]
}

TRIGGER_KEYWORDS = {
    'positive': ['happy', 'good', 'great', 'joy', 'smile', 'love', 'glad', 'positive'],
    'negative': ['sad', 'angry', 'cry', 'upset', 'depressed', 'bad day', 'unhappy', 'feeling down', 'tired'],
    'frustrated': ['frustrated', 'annoyed', 'irritated', 'mad', 'agitated'],
    'overwhelmed': ['overwhelmed', 'stressed', 'stressed out', 'burned out', 'tired', 'feeling down'],
}

ADVICE_RESPONSES = {
    'work': "If you're feeling sad about work, it might help to talk to someone about your feelings or consider making a plan to address what's bothering you.",
    'relationship': "If your feelings are related to a relationship, consider having an open conversation with the person involved.",
    'health': "If you're feeling down about your health, ensure you're taking care of yourself. Talk to a professional if needed.",
    'financial': "For financial worries, creating a budget or talking to a financial advisor could ease some stress.",
    'maintenance': "If it's about home maintenance, reaching out to a professional can help you feel more in control."
}

# Check for keywords in the message
def check_for_keywords(user_message):
    user_message = user_message.lower()
    for emotion, keywords in TRIGGER_KEYWORDS.items():
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', user_message):
                return emotion
    return None

# Analyze the emotion based on sentiment
def analyze_emotion(sia, user_message):
    sentiment_scores = sia.polarity_scores(user_message)
    if sentiment_scores['compound'] >= 0.5:
        return 'positive'
    elif sentiment_scores['compound'] <= -0.5:
        return 'negative'
    else:
        return 'neutral'

# Provide emotional support based on sentiment analysis and keyword check
def provide_emotional_support(user_message, context, sia):
    # Determine emotion from keywords or sentiment analysis
    emotion_from_keyword = check_for_keywords(user_message)
    emotion_from_sentiment = analyze_emotion(sia, user_message)

    # Prefer keyword detection if available
    if emotion_from_keyword:
        response = random.choice(EMOTIONAL_RESPONSES[emotion_from_keyword])
        context['last_topic'] = emotion_from_keyword
    else:
        response = random.choice(EMOTIONAL_RESPONSES[emotion_from_sentiment])
        context['last_topic'] = emotion_from_sentiment

    return response  # Make sure to return a string

def provide_advice(emotion, user_message):
    # Provide advice based on the emotional topic mentioned
    advice_responses = {
        'work': {
            'stress': "It's important to take breaks during your work. Consider organizing your tasks to make them more manageable.",
            'frustrated': "When work gets frustrating, try to focus on what you can control. Taking a walk might help clear your mind.",
            'sad': "If work is making you feel down, it might help to talk to your supervisor about your workload or seek support from colleagues."
        },
        'relationship': {
            'sad': "Talking to someone about your feelings can help. Consider reaching out to a friend or family member.",
            'frustrated': "Relationships can be tough. Open communication is key—try expressing your feelings honestly.",
        },
        'health': {
            'worried': "If you're feeling unwell, it's important to consult a professional. Make sure you're taking care of yourself.",
            'overwhelmed': "Self-care is crucial. Make time for rest and relaxation, and don't hesitate to ask for help if you need it.",
        },
        'financial': {
            'stressed': "Money issues can be stressful. Consider creating a budget or seeking advice from a financial advisor.",
            'worried': "It might help to write down your worries and see if there are actionable steps you can take."
        },
        'general': {
            'negative': "It's okay to feel down sometimes. Talking about it can really help.",
            'overwhelmed': "Take things one step at a time. Prioritize tasks and tackle them gradually."
        }
    }

    # Identify the topic of the user's message (You may want to customize this further)
    topic = None
    if 'work' in user_message.lower():
        topic = 'work'
    elif 'relationship' in user_message.lower():
        topic = 'relationship'
    elif 'health' in user_message.lower():
        topic = 'health'
    elif 'money' in user_message.lower() or 'financial' in user_message.lower():
        topic = 'financial'
    else:
        topic = 'general'

    # Return advice based on the identified emotion and topic
    return advice_responses.get(topic, {}).get(emotion, "I'm here to listen, and it's okay to talk about what's on your mind.")

# Adjust your main logic for processing messages
def handle_user_message(user_message, context, user_id, request):
    sia = SentimentIntensityAnalyzer()  # Initialize your sentiment analyzer
    response, updated_context = provide_emotional_support(user_message, context, sia)

    if context.get('last_topic'):
        # User has already mentioned an emotional topic; provide tailored advice
        advice = provide_advice(context['last_topic'], user_message)
        if advice:
            response = advice  # Update the response to be the tailored advice

    return response, updated_context
