from typing import Dict, List, Tuple
from app.schemas.assessment import (
    ProfileDeterminationResult, LeadershipProfile, LearningTrack, 
    ProfileDeterminationContent
)


# Profile determination content mapping
PROFILE_CONTENT_MAPPING = {
    ("clarity", "consistency"): {
        "growth_focus_summary": "You're currently navigating leadership without a clear anchor. You may feel pulled in multiple directions, often reacting to urgent needs while struggling to prioritize what truly matters. This can lead to decision fatigue and a lack of long-term direction for your team.",
        "intentional_advantage_summary": "You have created sustainable leadership rhythms. You show up with reliability, consistency, and steadiness. Now, you can expand your impact by teaching others how to lead with intention, not reaction."
    },
    ("clarity", "connection"): {
        "growth_focus_summary": "You're currently navigating leadership without a clear anchor. You may feel pulled in multiple directions, often reacting to urgent needs while struggling to prioritize what truly matters. This can lead to decision fatigue and a lack of long-term direction for your team.",
        "intentional_advantage_summary": "You lead with relational strength—creating safe spaces where others feel seen, heard, and valued. Your challenge now is to use that connection as a force for growth and accountability."
    },
    ("clarity", "courage"): {
        "growth_focus_summary": "You're currently navigating leadership without a clear anchor. You may feel pulled in multiple directions, often reacting to urgent needs while struggling to prioritize what truly matters. This can lead to decision fatigue and a lack of long-term direction for your team.",
        "intentional_advantage_summary": "You lead with courage—taking responsibility, acting with integrity, and addressing misalignment when it matters. Even when others hesitate, you speak up, hold boundaries, and model accountability."
    },
    ("clarity", "curiosity"): {
        "growth_focus_summary": "You're currently navigating leadership without a clear anchor. You may feel pulled in multiple directions, often reacting to urgent needs while struggling to prioritize what truly matters. This can lead to decision fatigue and a lack of long-term direction for your team.",
        "intentional_advantage_summary": "You ask questions that unlock insight, spark innovation, and resolve conflict. Your curiosity makes space for learning, humility, and creativity across your team."
    },
    ("consistency", "clarity"): {
        "growth_focus_summary": "You're leading from urgency and adrenaline—fighting fires instead of building systems. Without sustainable habits, you risk burnout and inconsistency for both you and your team.",
        "intentional_advantage_summary": "You prioritize what matters, connect daily actions to a clear purpose, and lead with vision. Your challenge is to help others get clear too—and to protect clarity in the chaos."
    },
    ("consistency", "connection"): {
        "growth_focus_summary": "You're leading from urgency and adrenaline—fighting fires instead of building systems. Without sustainable habits, you risk burnout and inconsistency for both you and your team.",
        "intentional_advantage_summary": "You lead with relational strength—creating safe spaces where others feel seen, heard, and valued. Your challenge now is to use that connection as a force for growth and accountability."
    },
    ("consistency", "courage"): {
        "growth_focus_summary": "You're leading from urgency and adrenaline—fighting fires instead of building systems. Without sustainable habits, you risk burnout and inconsistency for both you and your team.",
        "intentional_advantage_summary": "You lead with courage—taking responsibility, acting with integrity, and addressing misalignment when it matters. Even when others hesitate, you speak up, hold boundaries, and model accountability."
    },
    ("consistency", "curiosity"): {
        "growth_focus_summary": "You're leading from urgency and adrenaline—fighting fires instead of building systems. Without sustainable habits, you risk burnout and inconsistency for both you and your team.",
        "intentional_advantage_summary": "You ask questions that unlock insight, spark innovation, and resolve conflict. Your curiosity makes space for learning, humility, and creativity across your team."
    },
    ("connection", "clarity"): {
        "growth_focus_summary": "Even if well-intentioned, you may be operating without the emotional closeness or psychological safety your team needs. Connection is not about charisma—it's about consistency, trust, and care.",
        "intentional_advantage_summary": "You prioritize what matters, connect daily actions to a clear purpose, and lead with vision. Your challenge is to help others get clear too—and to protect clarity in the chaos."
    },
    ("connection", "consistency"): {
        "growth_focus_summary": "Even if well-intentioned, you may be operating without the emotional closeness or psychological safety your team needs. Connection is not about charisma—it's about consistency, trust, and care.",
        "intentional_advantage_summary": "You have created sustainable leadership rhythms. You show up with reliability, consistency, and steadiness. Now, you can expand your impact by teaching others how to lead with intention, not reaction."
    },
    ("connection", "courage"): {
        "growth_focus_summary": "Even if well-intentioned, you may be operating without the emotional closeness or psychological safety your team needs. Connection is not about charisma—it's about consistency, trust, and care.",
        "intentional_advantage_summary": "You lead with courage—taking responsibility, acting with integrity, and addressing misalignment when it matters. Even when others hesitate, you speak up, hold boundaries, and model accountability."
    },
    ("connection", "curiosity"): {
        "growth_focus_summary": "Even if well-intentioned, you may be operating without the emotional closeness or psychological safety your team needs. Connection is not about charisma—it's about consistency, trust, and care.",
        "intentional_advantage_summary": "You ask questions that unlock insight, spark innovation, and resolve conflict. Your curiosity makes space for learning, humility, and creativity across your team."
    },
    ("courage", "clarity"): {
        "growth_focus_summary": "You value peace and stability—but it may be coming at a cost. Avoiding difficult conversations or shying away from accountability can erode clarity and breed frustration under the surface.",
        "intentional_advantage_summary": "You prioritize what matters, connect daily actions to a clear purpose, and lead with vision. Your challenge is to help others get clear too—and to protect clarity in the chaos."
    },
    ("courage", "consistency"): {
        "growth_focus_summary": "You value peace and stability—but it may be coming at a cost. Avoiding difficult conversations or shying away from accountability can erode clarity and breed frustration under the surface.",
        "intentional_advantage_summary": "You have created sustainable leadership rhythms. You show up with reliability, consistency, and steadiness. Now, you can expand your impact by teaching others how to lead with intention, not reaction."
    },
    ("courage", "connection"): {
        "growth_focus_summary": "You value peace and stability—but it may be coming at a cost. Avoiding difficult conversations or shying away from accountability can erode clarity and breed frustration under the surface.",
        "intentional_advantage_summary": "You lead with relational strength—creating safe spaces where others feel seen, heard, and valued. Your challenge now is to use that connection as a force for growth and accountability."
    },
    ("courage", "curiosity"): {
        "growth_focus_summary": "You value peace and stability—but it may be coming at a cost. Avoiding difficult conversations or shying away from accountability can erode clarity and breed frustration under the surface.",
        "intentional_advantage_summary": "You ask questions that unlock insight, spark innovation, and resolve conflict. Your curiosity makes space for learning, humility, and creativity across your team."
    },
    ("curiosity", "clarity"): {
        "growth_focus_summary": "You may be approaching leadership with a rigid lens—missing the opportunity to explore new perspectives. Without curiosity, conflict becomes personal and learning stagnates.",
        "intentional_advantage_summary": "You prioritize what matters, connect daily actions to a clear purpose, and lead with vision. Your challenge is to help others get clear too—and to protect clarity in the chaos."
    },
    ("curiosity", "consistency"): {
        "growth_focus_summary": "You may be approaching leadership with a rigid lens—missing the opportunity to explore new perspectives. Without curiosity, conflict becomes personal and learning stagnates.",
        "intentional_advantage_summary": "You have created sustainable leadership rhythms. You show up with reliability, consistency, and steadiness. Now, you can expand your impact by teaching others how to lead with intention, not reaction."
    },
    ("curiosity", "connection"): {
        "growth_focus_summary": "You may be approaching leadership with a rigid lens—missing the opportunity to explore new perspectives. Without curiosity, conflict becomes personal and learning stagnates.",
        "intentional_advantage_summary": "You lead with relational strength—creating safe spaces where others feel seen, heard, and valued. Your challenge now is to use that connection as a force for growth and accountability."
    },
    ("curiosity", "courage"): {
        "growth_focus_summary": "You may be approaching leadership with a rigid lens—missing the opportunity to explore new perspectives. Without curiosity, conflict becomes personal and learning stagnates.",
        "intentional_advantage_summary": "You lead with courage—taking responsibility, acting with integrity, and addressing misalignment when it matters. Even when others hesitate, you speak up, hold boundaries, and model accountability."
    },
    ("balanced", "balanced"): {
        "growth_focus_summary": "You've demonstrated strong leadership habits across all five dimensions. You're likely operating with a strong sense of purpose and modeling intentionality in your daily actions.",
        "intentional_advantage_summary": "Now is the time to scale your impact—mentor others, deepen your mastery, and explore the next layer of your purpose."
    }
}


# Leadership type mapping based on intentional advantage
LEADERSHIP_TYPE_MAPPING = {
    "clarity": {
        "primary_type": "VISIONARY LEADER",
        "description": "You excel at creating clear direction and purpose. Your strength lies in connecting daily actions to meaningful goals.",
        "strengths": [
            "Strategic thinking & vision setting",
            "Clear communication & purpose alignment",
            "Goal-oriented decision making",
            "Long-term planning & direction"
        ],
        "areas_for_development": [
            "Building sustainable systems",
            "Creating psychological safety",
            "Having difficult conversations",
            "Embracing diverse perspectives"
        ]
    },
    "consistency": {
        "primary_type": "STEADY LEADER",
        "description": "You excel at creating reliable systems and sustainable habits. Your strength lies in building stability and trust.",
        "strengths": [
            "Reliable systems & processes",
            "Sustainable leadership habits",
            "Team stability & predictability",
            "Work-life balance modeling"
        ],
        "areas_for_development": [
            "Strategic vision setting",
            "Building deep connections",
            "Courageous conversations",
            "Innovation & adaptability"
        ]
    },
    "connection": {
        "primary_type": "COLLABORATIVE LEADER",
        "description": "You excel at bringing people together and building consensus. Your strength lies in creating inclusive environments.",
        "strengths": [
            "Team building & relationship management",
            "Active listening & empathy",
            "Conflict resolution",
            "Inclusive decision making"
        ],
        "areas_for_development": [
            "Decisive leadership in crisis",
            "Setting firm boundaries",
            "Time management & prioritization",
            "Difficult conversations"
        ]
    },
    "courage": {
        "primary_type": "BOLD LEADER",
        "description": "You excel at taking responsibility and addressing challenges head-on. Your strength lies in modeling accountability.",
        "strengths": [
            "Accountability & responsibility",
            "Difficult conversation mastery",
            "Boundary setting & integrity",
            "Crisis leadership"
        ],
        "areas_for_development": [
            "Building psychological safety",
            "Strategic thinking & planning",
            "Sustainable systems creation",
            "Empathetic communication"
        ]
    },
    "curiosity": {
        "primary_type": "INNOVATIVE LEADER",
        "description": "You excel at asking powerful questions and fostering learning. Your strength lies in creating space for growth and creativity.",
        "strengths": [
            "Questioning & inquiry skills",
            "Learning facilitation",
            "Innovation & creativity",
            "Conflict resolution through understanding"
        ],
        "areas_for_development": [
            "Decisive action taking",
            "Clear direction setting",
            "Consistent follow-through",
            "Building trust through reliability"
        ]
    },
    "balanced": {
        "primary_type": "INTEGRATED LEADER",
        "description": "You demonstrate balanced leadership across all dimensions. Your strength lies in your comprehensive approach to leadership.",
        "strengths": [
            "Balanced leadership approach",
            "Comprehensive skill development",
            "Adaptable leadership style",
            "Mentoring & development of others"
        ],
        "areas_for_development": [
            "Scaling impact through others",
            "Deepening mastery in chosen areas",
            "Exploring next-level purpose",
            "Leading organizational transformation"
        ]
    }
}


# Learning tracks mapping
LEARNING_TRACKS_MAPPING = {
    "clarity": [
        LearningTrack(title="STRATEGIC VISION", description="Develop skills in long-term planning and purpose-driven leadership", is_recommended=True),
        LearningTrack(title="DECISIVE LEADERSHIP", description="Build confidence in making tough decisions quickly and effectively", is_recommended=False),
        LearningTrack(title="DIFFICULT CONVERSATIONS", description="Master challenging discussions with confidence and clarity", is_recommended=False)
    ],
    "consistency": [
        LearningTrack(title="SYSTEMS BUILDING", description="Create sustainable processes and reliable leadership habits", is_recommended=True),
        LearningTrack(title="BOUNDARY SETTING", description="Learn to set clear expectations while preserving relationships", is_recommended=False),
        LearningTrack(title="STRATEGIC VISION", description="Develop skills in long-term planning and purpose-driven leadership", is_recommended=False)
    ],
    "connection": [
        LearningTrack(title="BOUNDARY SETTING", description="Learn to set clear expectations while preserving relationships", is_recommended=True),
        LearningTrack(title="DECISIVE LEADERSHIP", description="Build confidence in making tough decisions quickly and effectively", is_recommended=False),
        LearningTrack(title="DIFFICULT CONVERSATIONS", description="Master challenging discussions with confidence and clarity", is_recommended=False)
    ],
    "courage": [
        LearningTrack(title="DIFFICULT CONVERSATIONS", description="Master challenging discussions with confidence and clarity", is_recommended=True),
        LearningTrack(title="BOUNDARY SETTING", description="Learn to set clear expectations while preserving relationships", is_recommended=False),
        LearningTrack(title="STRATEGIC VISION", description="Develop skills in long-term planning and purpose-driven leadership", is_recommended=False)
    ],
    "curiosity": [
        LearningTrack(title="DECISIVE LEADERSHIP", description="Build confidence in making tough decisions quickly and effectively", is_recommended=True),
        LearningTrack(title="STRATEGIC VISION", description="Develop skills in long-term planning and purpose-driven leadership", is_recommended=False),
        LearningTrack(title="BOUNDARY SETTING", description="Learn to set clear expectations while preserving relationships", is_recommended=False)
    ],
    "balanced": [
        LearningTrack(title="MENTORING MASTERY", description="Develop advanced skills in developing and scaling others", is_recommended=True),
        LearningTrack(title="ORGANIZATIONAL TRANSFORMATION", description="Lead large-scale change and cultural evolution", is_recommended=False),
        LearningTrack(title="PURPOSE EXPLORATION", description="Deepen your understanding of personal and organizational purpose", is_recommended=False)
    ]
}


def determine_profile(category_scores: Dict[str, int], is_balanced: bool = False) -> ProfileDeterminationResult:
    """
    Determine the user's leadership profile based on their 5Cs assessment scores.
    
    Args:
        category_scores: Dictionary with scores for each category
        is_balanced: Whether the user is a balanced leader
        
    Returns:
        ProfileDeterminationResult with complete profile information
    """
    
    if is_balanced:
        growth_focus = "balanced"
        intentional_advantage = "balanced"
    else:
        # Find the lowest scoring category (growth focus)
        growth_focus = min(category_scores, key=category_scores.get)
        
        # Find the highest scoring category (intentional advantage)
        intentional_advantage = max(category_scores, key=category_scores.get)
    
    # Get profile content
    content_key = (growth_focus, intentional_advantage)
    profile_content_data = PROFILE_CONTENT_MAPPING.get(content_key, {
        "growth_focus_summary": "Focus on developing your leadership skills in this area.",
        "intentional_advantage_summary": "Leverage your strengths in this area to create greater impact."
    })
    
    # Get leadership type information
    leadership_type_data = LEADERSHIP_TYPE_MAPPING.get(intentional_advantage, LEADERSHIP_TYPE_MAPPING["balanced"])
    
    # Get learning tracks
    learning_tracks = LEARNING_TRACKS_MAPPING.get(intentional_advantage, LEARNING_TRACKS_MAPPING["balanced"])
    
    # Create profile content
    profile_content = ProfileDeterminationContent(
        growth_focus_summary=profile_content_data["growth_focus_summary"],
        intentional_advantage_summary=profile_content_data["intentional_advantage_summary"]
    )
    
    # Create leadership profile
    leadership_profile = LeadershipProfile(
        primary_type=leadership_type_data["primary_type"],
        description=leadership_type_data["description"],
        strengths=leadership_type_data["strengths"],
        areas_for_development=leadership_type_data["areas_for_development"],
        learning_tracks=learning_tracks,
        profile_content=profile_content
    )
    
    return ProfileDeterminationResult(
        leadership_profile=leadership_profile,
        category_scores=category_scores,
        growth_focus=growth_focus,
        intentional_advantage=intentional_advantage,
        is_balanced_leader=is_balanced
    )
