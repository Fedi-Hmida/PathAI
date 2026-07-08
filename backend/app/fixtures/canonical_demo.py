from __future__ import annotations

from datetime import UTC, datetime

from app.schemas.adaptation import AdaptationEventDTO
from app.schemas.assessment import (
    AssessmentAnswerDTO,
    AssessmentQuestionDTO,
    AssessmentSessionDTO,
    ConceptEvidence,
    ConceptEvidenceUpdate,
)
from app.schemas.critic import CriticDimensionScores, CriticReviewDTO
from app.schemas.curriculum import (
    CurriculumChangeDTO,
    CurriculumDTO,
    CurriculumTopicDTO,
    CurriculumWeekDTO,
)
from app.schemas.dashboard import (
    AdaptationSummary,
    CurriculumSummary,
    CurriculumWeekSummary,
    DashboardPayload,
    DashboardUIFlags,
    EvaluationSummary,
    GoalSummary,
    KnowledgeMapSummary,
    ProgressSummary,
    QuizSummary,
    ResourcesSummary,
    RunSummary,
)
from app.schemas.enums import (
    AdaptationStatus,
    AdaptationTriggerType,
    ConceptClassification,
    CriticPassStatus,
    CurriculumChangeType,
    CurriculumStatus,
    DifficultyLevel,
    EvaluationPassStatus,
    ExecutionMode,
    GoalStatus,
    KnowledgeMapStatus,
    OrchestrationStatus,
    ProgressStatus,
    QuestionType,
    QuizAttemptStatus,
    QuizStatus,
    ResourceAttachmentStatus,
    ResourceStatus,
    ResourceType,
    ScoringPolicyType,
    TopicProgressStatus,
)
from app.schemas.evaluation import EvaluationMetricScores, EvaluationReportDTO
from app.schemas.goal import LearnerProfile, LearningGoalDTO
from app.schemas.knowledge_map import ConceptMasteryDTO, KnowledgeMapDTO
from app.schemas.progress import (
    NextRecommendedAction,
    ProgressStateDTO,
    StuckEventDTO,
    TopicProgressDTO,
)
from app.schemas.quiz import (
    ConceptQuizScore,
    QuizAnswerSubmission,
    QuizAttemptDTO,
    QuizDTO,
    QuizQuestionDTO,
    QuizScoringPolicy,
)
from app.schemas.resource import ResourceAttachmentDTO, ResourceDTO

NOW = datetime(2026, 7, 5, 12, 0, tzinfo=UTC)

CANONICAL_GOAL_TEXT = "Learn RAG systems for an AI engineering graduation project"
RUN_ID = "run_demo_rag"
GOAL_ID = "goal_demo_rag"
ASSESSMENT_ID = "assessment_demo_rag"
KNOWLEDGE_MAP_ID = "kmap_demo_rag"
CURRICULUM_ID = "curriculum_demo_rag_v1"
PROGRESS_ID = "progress_demo_rag"
QUIZ_ID = "quiz_demo_rag"
QUIZ_ATTEMPT_ID = "attempt_demo_rag_low_score"
ADAPTATION_ID = "adapt_demo_rag_retrieval"
CRITIC_REVIEW_ID = "critic_demo_rag"
EVALUATION_REPORT_ID = "eval_demo_rag"

LEARNER_PROFILE = LearnerProfile(
    learner_type="final-year AI engineering student",
    strengths=["python_basics", "machine_learning_basics", "api_basics"],
    weak_areas=["vector_search", "chunking", "retrieval_evaluation"],
    time_availability_hours_per_week=7,
    desired_outcome="Build and explain a credible RAG subsystem for a graduation project.",
    preferred_resource_types=["documentation", "tutorial", "paper", "code_example", "exercise"],
    difficulty_target=DifficultyLevel.INTERMEDIATE,
)

LEARNING_GOAL = LearningGoalDTO(
    goal_id=GOAL_ID,
    run_id=RUN_ID,
    goal_text=CANONICAL_GOAL_TEXT,
    normalized_goal_text=CANONICAL_GOAL_TEXT,
    status=GoalStatus.ACTIVE,
    learner_profile=LEARNER_PROFILE,
    target_duration_weeks=4,
    hours_per_week=7,
    demo_seed_id="demo_rag_systems",
    created_at=NOW,
    updated_at=NOW,
)

ASSESSMENT_QUESTIONS = [
    AssessmentQuestionDTO(
        question_id="question_assess_retriever_role",
        question_type=QuestionType.MULTIPLE_CHOICE,
        prompt="Which component finds relevant documents in a RAG pipeline?",
        options=["Retriever", "Tokenizer", "Optimizer", "Frontend router"],
        target_concepts=["rag_fundamentals", "retrieval"],
        difficulty=DifficultyLevel.BEGINNER,
    ),
    AssessmentQuestionDTO(
        question_id="question_assess_recall_at_k",
        question_type=QuestionType.SHORT_ANSWER,
        prompt="Explain what recall at k measures in retrieval evaluation.",
        target_concepts=["retrieval_evaluation"],
        difficulty=DifficultyLevel.INTERMEDIATE,
    ),
    AssessmentQuestionDTO(
        question_id="question_assess_chunking",
        question_type=QuestionType.MULTIPLE_CHOICE,
        prompt="Why can chunk size affect retrieval quality?",
        options=[
            "It changes context granularity",
            "It removes the need for embeddings",
            "It replaces evaluation",
            "It only affects frontend layout",
        ],
        target_concepts=["chunking", "retrieval"],
        difficulty=DifficultyLevel.INTERMEDIATE,
    ),
    AssessmentQuestionDTO(
        question_id="question_assess_embeddings",
        question_type=QuestionType.SELF_RATING,
        prompt="Rate your confidence explaining embeddings for semantic retrieval.",
        target_concepts=["embeddings", "vector_search"],
        difficulty=DifficultyLevel.INTERMEDIATE,
    ),
    AssessmentQuestionDTO(
        question_id="question_assess_failures",
        question_type=QuestionType.SHORT_ANSWER,
        prompt="Name one production failure mode for a RAG system.",
        target_concepts=["production_rag_failures", "hallucination_reduction"],
        difficulty=DifficultyLevel.ADVANCED,
    ),
]

CONCEPT_EVIDENCE = [
    ConceptEvidence(
        concept_id="rag_fundamentals",
        score=0.82,
        evidence=["Identified retriever role correctly."],
    ),
    ConceptEvidence(
        concept_id="api_basics",
        score=0.78,
        evidence=["Comfortable with backend API concepts."],
    ),
    ConceptEvidence(
        concept_id="retrieval_evaluation",
        score=0.28,
        evidence=["Could not clearly distinguish recall at k from answer quality."],
    ),
    ConceptEvidence(
        concept_id="vector_search",
        score=0.32,
        evidence=["Uncertain about embedding similarity and index behavior."],
    ),
]

ASSESSMENT_SESSION = AssessmentSessionDTO(
    assessment_session_id=ASSESSMENT_ID,
    goal_id=GOAL_ID,
    run_id=RUN_ID,
    status="completed",
    question_count=len(ASSESSMENT_QUESTIONS),
    confidence=0.78,
    concept_evidence=CONCEPT_EVIDENCE,
    started_at=NOW,
    completed_at=NOW,
    termination_reason="confidence_target_met",
    created_at=NOW,
    updated_at=NOW,
)

ASSESSMENT_ANSWERS = [
    AssessmentAnswerDTO(
        answer_id="answer_demo_retriever_role",
        assessment_session_id=ASSESSMENT_ID,
        goal_id=GOAL_ID,
        question=ASSESSMENT_QUESTIONS[0],
        selected_options=["Retriever"],
        score=1.0,
        concept_scores=[
            ConceptEvidenceUpdate(
                concept_id="rag_fundamentals",
                score_delta=0.2,
                evidence="Correctly identified retrieval responsibility.",
            )
        ],
        feedback="Strong understanding of the retriever role.",
        created_at=NOW,
        updated_at=NOW,
    ),
    AssessmentAnswerDTO(
        answer_id="answer_demo_recall_at_k",
        assessment_session_id=ASSESSMENT_ID,
        goal_id=GOAL_ID,
        question=ASSESSMENT_QUESTIONS[1],
        answer_text="It checks if answers are good.",
        score=0.25,
        concept_scores=[
            ConceptEvidenceUpdate(
                concept_id="retrieval_evaluation",
                score_delta=-0.3,
                evidence="Confused retrieval quality with final answer quality.",
            )
        ],
        feedback="Needs targeted practice with retrieval metrics.",
        created_at=NOW,
        updated_at=NOW,
    ),
]

KNOWLEDGE_MAP = KnowledgeMapDTO(
    knowledge_map_id=KNOWLEDGE_MAP_ID,
    goal_id=GOAL_ID,
    assessment_session_id=ASSESSMENT_ID,
    run_id=RUN_ID,
    status=KnowledgeMapStatus.ACTIVE,
    concepts=[
        ConceptMasteryDTO(
            concept_id="rag_fundamentals",
            label="RAG fundamentals",
            mastery_score=0.82,
            classification=ConceptClassification.STRONG,
            evidence=["Understands retriever and generator roles."],
        ),
        ConceptMasteryDTO(
            concept_id="retrieval_evaluation",
            label="Retrieval evaluation",
            mastery_score=0.28,
            classification=ConceptClassification.WEAK,
            evidence=["Needs recall and precision metric practice."],
            recommended_action="Add retrieval metrics practice before project integration.",
        ),
        ConceptMasteryDTO(
            concept_id="vector_search",
            label="Vector search",
            mastery_score=0.32,
            classification=ConceptClassification.WEAK,
            evidence=["Needs support with similarity search behavior."],
        ),
        ConceptMasteryDTO(
            concept_id="chunking",
            label="Chunking strategy",
            mastery_score=0.48,
            classification=ConceptClassification.DEVELOPING,
            evidence=["Recognizes chunk size matters but needs practical heuristics."],
        ),
    ],
    strong_concepts=["rag_fundamentals", "api_basics"],
    developing_concepts=["chunking", "embeddings"],
    weak_concepts=["retrieval_evaluation", "vector_search"],
    missing_concepts=["reranking", "production_rag_failures"],
    confidence=0.78,
    summary="The learner has strong high-level RAG knowledge but needs retrieval metrics practice.",
    created_at=NOW,
    updated_at=NOW,
)

TOPICS = [
    CurriculumTopicDTO(
        topic_id="topic_rag_foundations",
        title="RAG foundations and grounding",
        description="Review how retrieval augments generation and why grounding matters.",
        concept_ids=["rag_fundamentals", "retrieval"],
        difficulty=DifficultyLevel.BEGINNER,
        estimated_hours=2.0,
        learning_outcomes=["Explain the retriever role in a RAG system."],
        sequence_order=1,
        practice_task="Sketch a simple RAG request flow.",
    ),
    CurriculumTopicDTO(
        topic_id="topic_chunking_strategy",
        title="Chunking strategy",
        description="Compare chunk sizes and overlap for retrieval quality.",
        concept_ids=["chunking", "retrieval"],
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_hours=2.0,
        learning_outcomes=["Choose a chunking approach for project documents."],
        sequence_order=2,
    ),
    CurriculumTopicDTO(
        topic_id="topic_vector_search",
        title="Vector search basics",
        description="Connect embeddings, similarity search, and vector indexes.",
        concept_ids=["embeddings", "vector_search"],
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_hours=3.0,
        learning_outcomes=["Explain why embedding choice affects retrieval."],
        sequence_order=3,
    ),
    CurriculumTopicDTO(
        topic_id="topic_retrieval_metrics",
        title="Retrieval metrics practice",
        description="Practice recall at k and precision at k with toy retrieval results.",
        concept_ids=["retrieval_evaluation"],
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_hours=3.0,
        learning_outcomes=["Compute recall at k for a small retrieval dataset."],
        sequence_order=4,
        assessment_checkpoint="Retrieval metrics quiz",
    ),
    CurriculumTopicDTO(
        topic_id="topic_production_rag",
        title="Production RAG failure modes",
        description="Identify failure modes and mitigations for deployed RAG systems.",
        concept_ids=["production_rag_failures", "hallucination_reduction"],
        difficulty=DifficultyLevel.ADVANCED,
        estimated_hours=3.0,
        learning_outcomes=["Describe two production RAG risks and mitigations."],
        sequence_order=5,
    ),
]

CURRICULUM_WEEKS = [
    CurriculumWeekDTO(
        week_id="week_demo_1",
        week_number=1,
        theme="RAG foundations and document preparation",
        topics=[TOPICS[0], TOPICS[1]],
        estimated_hours=4.0,
        learning_outcomes=["Explain RAG grounding and prepare documents for retrieval."],
    ),
    CurriculumWeekDTO(
        week_id="week_demo_2",
        week_number=2,
        theme="Embeddings, vector search, and retrieval metrics",
        topics=[TOPICS[2], TOPICS[3]],
        estimated_hours=6.0,
        learning_outcomes=["Evaluate retrieval quality with simple metrics."],
    ),
    CurriculumWeekDTO(
        week_id="week_demo_3",
        week_number=3,
        theme="Prompt augmentation and reliability",
        topics=[TOPICS[4]],
        estimated_hours=3.0,
        learning_outcomes=["Reduce hallucination risk with grounded context."],
    ),
    CurriculumWeekDTO(
        week_id="week_demo_4",
        week_number=4,
        theme="Graduation project integration",
        topics=[
            CurriculumTopicDTO(
                topic_id="topic_fastapi_rag_integration",
                title="FastAPI RAG integration",
                description="Expose a small RAG retrieval endpoint for the graduation project.",
                concept_ids=["api_basics", "system_design"],
                difficulty=DifficultyLevel.INTERMEDIATE,
                estimated_hours=4.0,
                learning_outcomes=["Connect a backend endpoint to a retrieval component."],
                sequence_order=6,
            )
        ],
        estimated_hours=4.0,
        learning_outcomes=["Integrate and explain the RAG subsystem architecture."],
        milestone="Present a working RAG subsystem walkthrough.",
    ),
]

CURRICULUM = CurriculumDTO(
    curriculum_id=CURRICULUM_ID,
    goal_id=GOAL_ID,
    knowledge_map_id=KNOWLEDGE_MAP_ID,
    run_id=RUN_ID,
    status=CurriculumStatus.ACTIVE,
    title="Four-Week RAG Systems Build Plan",
    duration_weeks=4,
    weeks=CURRICULUM_WEEKS,
    target_outcomes=["Build a small RAG subsystem.", "Explain retrieval evaluation tradeoffs."],
    assumptions=["The learner can write Python functions and call backend endpoints."],
    critic_revision_attempt=0,
    created_at=NOW,
    updated_at=NOW,
)

RESOURCE_CORPUS = [
    ResourceDTO(
        resource_id="resource_rag_intro",
        title="RAG systems introduction",
        resource_type=ResourceType.ARTICLE,
        source_name="PathAI curated corpus",
        url="https://example.org/pathai/rag-introduction",
        topic_tags=["rag", "retrieval"],
        concept_ids=["rag_fundamentals", "retrieval"],
        difficulty=DifficultyLevel.BEGINNER,
        estimated_minutes=35,
        quality_score=0.9,
        license_note="Public educational reference.",
        status=ResourceStatus.ACTIVE,
        summary="A concise overview of retrieval-augmented generation components.",
        created_at=NOW,
        updated_at=NOW,
    ),
    ResourceDTO(
        resource_id="resource_retrieval_metrics",
        title="Retrieval metrics practice lab",
        resource_type=ResourceType.EXERCISE,
        source_name="PathAI curated corpus",
        url="https://example.org/pathai/retrieval-metrics-lab",
        topic_tags=["evaluation", "retrieval"],
        concept_ids=["retrieval_evaluation"],
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_minutes=45,
        quality_score=0.92,
        license_note="Public educational exercise.",
        status=ResourceStatus.ACTIVE,
        summary="Hands-on recall and precision practice for retrieval outputs.",
        created_at=NOW,
        updated_at=NOW,
    ),
    ResourceDTO(
        resource_id="resource_vector_search",
        title="Vector search concepts",
        resource_type=ResourceType.DOCUMENTATION,
        source_name="PathAI curated corpus",
        url="https://example.org/pathai/vector-search-concepts",
        topic_tags=["embeddings", "vector_search"],
        concept_ids=["embeddings", "vector_search"],
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_minutes=40,
        quality_score=0.88,
        license_note="Public educational reference.",
        status=ResourceStatus.ACTIVE,
        summary="A guided explanation of embedding similarity and vector search behavior.",
        created_at=NOW,
        updated_at=NOW,
    ),
    ResourceDTO(
        resource_id="resource_chunking_tutorial",
        title="Chunking strategy tutorial",
        resource_type=ResourceType.TUTORIAL,
        source_name="PathAI curated corpus",
        url="https://example.org/pathai/chunking-strategy-tutorial",
        topic_tags=["chunking", "retrieval"],
        concept_ids=["chunking", "retrieval"],
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_minutes=35,
        quality_score=0.87,
        license_note="Public educational tutorial.",
        status=ResourceStatus.ACTIVE,
        summary="A practical tutorial for chunk size, overlap, and retrieval granularity.",
        created_at=NOW,
        updated_at=NOW,
    ),
    ResourceDTO(
        resource_id="resource_reranking_paper",
        title="Reranking for retrieval quality",
        resource_type=ResourceType.PAPER,
        source_name="PathAI curated corpus",
        url="https://example.org/pathai/reranking-retrieval-quality",
        topic_tags=["reranking", "evaluation", "retrieval"],
        concept_ids=["reranking", "retrieval_evaluation"],
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_minutes=50,
        quality_score=0.86,
        license_note="Public educational paper summary.",
        status=ResourceStatus.ACTIVE,
        summary="A short paper-style resource on reranking retrieved passages.",
        created_at=NOW,
        updated_at=NOW,
    ),
    ResourceDTO(
        resource_id="resource_production_rag_video",
        title="Production RAG failure modes walkthrough",
        resource_type=ResourceType.VIDEO,
        source_name="PathAI curated corpus",
        url="https://example.org/pathai/production-rag-failures-video",
        topic_tags=["production", "rag", "hallucination"],
        concept_ids=["production_rag_failures", "hallucination_reduction"],
        difficulty=DifficultyLevel.ADVANCED,
        estimated_minutes=30,
        quality_score=0.84,
        license_note="Public educational video.",
        status=ResourceStatus.ACTIVE,
        summary="A concise walkthrough of failure modes in deployed RAG systems.",
        created_at=NOW,
        updated_at=NOW,
    ),
    ResourceDTO(
        resource_id="resource_fastapi_rag_code",
        title="FastAPI RAG endpoint example",
        resource_type=ResourceType.CODE_EXAMPLE,
        source_name="PathAI curated corpus",
        url="https://example.org/pathai/fastapi-rag-endpoint-example",
        topic_tags=["fastapi", "api", "system_design"],
        concept_ids=["api_basics", "system_design"],
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_minutes=45,
        quality_score=0.89,
        license_note="Public educational code example.",
        status=ResourceStatus.ACTIVE,
        summary="A small code example for connecting a backend endpoint to retrieval.",
        created_at=NOW,
        updated_at=NOW,
    ),
]

RESOURCE_ATTACHMENTS = [
    ResourceAttachmentDTO(
        attachment_id="attach_rag_intro",
        goal_id=GOAL_ID,
        curriculum_id=CURRICULUM_ID,
        topic_id="topic_rag_foundations",
        resource_id="resource_rag_intro",
        rank=1,
        relevance_score=0.91,
        selection_reason="Matches RAG fundamentals and retrieval at beginner difficulty.",
        quality_score_snapshot=0.9,
        diversity_category="article",
        status=ResourceAttachmentStatus.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
    ),
    ResourceAttachmentDTO(
        attachment_id="attach_retrieval_metrics",
        goal_id=GOAL_ID,
        curriculum_id=CURRICULUM_ID,
        topic_id="topic_retrieval_metrics",
        resource_id="resource_retrieval_metrics",
        rank=1,
        relevance_score=0.94,
        selection_reason="Targets the weak retrieval evaluation concept directly.",
        quality_score_snapshot=0.92,
        diversity_category="exercise",
        status=ResourceAttachmentStatus.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
    ),
]

PROGRESS_STATE = ProgressStateDTO(
    progress_state_id=PROGRESS_ID,
    goal_id=GOAL_ID,
    curriculum_id=CURRICULUM_ID,
    status=ProgressStatus.ADAPTATION_NEEDED,
    overall_completion=0.25,
    current_topic_id="topic_retrieval_metrics",
    topic_progress=[
        TopicProgressDTO(
            topic_id="topic_rag_foundations",
            status=TopicProgressStatus.COMPLETED,
            completion=1.0,
            last_score=0.9,
            attempt_count=1,
            completed_at=NOW,
        ),
        TopicProgressDTO(
            topic_id="topic_retrieval_metrics",
            status=TopicProgressStatus.NEEDS_REVIEW,
            completion=0.4,
            last_score=0.4,
            attempt_count=1,
            stuck_count=1,
        ),
    ],
    weak_concepts=["retrieval_evaluation", "vector_search"],
    stuck_events=[
        StuckEventDTO(
            topic_id="topic_retrieval_metrics",
            concept_ids=["retrieval_evaluation"],
            reason="Quiz result shows weak retrieval metric understanding.",
            created_at=NOW,
        )
    ],
    last_activity_at=NOW,
    next_recommended_action=NextRecommendedAction(
        topic_id="topic_retrieval_metrics",
        label="Review retrieval metrics practice",
        reason="Retrieval evaluation is below the adaptation threshold.",
    ),
    created_at=NOW,
    updated_at=NOW,
)

QUIZ_QUESTIONS = [
    QuizQuestionDTO(
        question_id="question_quiz_recall_k",
        question_type=QuestionType.MULTIPLE_CHOICE,
        prompt="What does recall at k measure?",
        options=[
            "Relevant items appearing in the top k retrieved results",
            "Final answer fluency",
            "Number of generated tokens",
            "Frontend response speed",
        ],
        correct_answer="Relevant items appearing in the top k retrieved results",
        concept_ids=["retrieval_evaluation"],
        difficulty=DifficultyLevel.INTERMEDIATE,
        points=1.0,
        explanation="Recall at k measures whether relevant items are retrieved within top k.",
    ),
    QuizQuestionDTO(
        question_id="question_quiz_vector_search",
        question_type=QuestionType.SHORT_ANSWER,
        prompt="Why do embeddings matter for vector search?",
        correct_answer="They place similar meanings near each other for retrieval.",
        concept_ids=["embeddings", "vector_search"],
        difficulty=DifficultyLevel.INTERMEDIATE,
        points=1.0,
    ),
    QuizQuestionDTO(
        question_id="question_quiz_chunking",
        question_type=QuestionType.MULTIPLE_CHOICE,
        prompt="What is a common chunking tradeoff?",
        options=[
            "Granularity versus context completeness",
            "Authentication versus authorization",
            "Color palette versus layout",
            "Deployment versus billing",
        ],
        correct_answer="Granularity versus context completeness",
        concept_ids=["chunking"],
        difficulty=DifficultyLevel.INTERMEDIATE,
        points=1.0,
    ),
]

QUIZ = QuizDTO(
    quiz_id=QUIZ_ID,
    goal_id=GOAL_ID,
    curriculum_id=CURRICULUM_ID,
    target_topic_ids=["topic_retrieval_metrics", "topic_vector_search"],
    target_concept_ids=["retrieval_evaluation", "vector_search"],
    status=QuizStatus.COMPLETED,
    title="RAG Retrieval Checkpoint",
    questions=QUIZ_QUESTIONS,
    scoring_policy=QuizScoringPolicy(type=ScoringPolicyType.EXACT_MATCH, partial_credit=False),
    difficulty=DifficultyLevel.INTERMEDIATE,
    created_at=NOW,
    updated_at=NOW,
)

QUIZ_ATTEMPT = QuizAttemptDTO(
    quiz_attempt_id=QUIZ_ATTEMPT_ID,
    quiz_id=QUIZ_ID,
    goal_id=GOAL_ID,
    curriculum_id=CURRICULUM_ID,
    answers=[
        QuizAnswerSubmission(
            question_id="question_quiz_recall_k",
            selected_options=["Final answer fluency"],
        ),
        QuizAnswerSubmission(
            question_id="question_quiz_vector_search",
            answer_text="They make storage faster.",
        ),
        QuizAnswerSubmission(
            question_id="question_quiz_chunking",
            selected_options=["Granularity versus context completeness"],
        ),
    ],
    total_score=0.33,
    correct_count=1,
    total_questions=3,
    concept_scores=[
        ConceptQuizScore(
            concept_id="retrieval_evaluation",
            score=0.0,
            correct_count=0,
            total_questions=1,
        ),
        ConceptQuizScore(
            concept_id="vector_search",
            score=0.3,
            correct_count=0,
            total_questions=1,
        ),
    ],
    weak_concepts=["retrieval_evaluation", "vector_search"],
    submitted_at=NOW,
    status=QuizAttemptStatus.SCORED,
    feedback="Review retrieval metrics and vector search fundamentals before continuing.",
    adaptation_triggered=True,
    created_at=NOW,
    updated_at=NOW,
)

ADAPTATION_CHANGE = CurriculumChangeDTO(
    change_type=CurriculumChangeType.INSERT_TOPIC,
    target_week=2,
    affected_topic_ids=["topic_retrieval_metrics"],
    affected_concept_ids=["retrieval_evaluation"],
    reason="Quiz score was below the adaptation threshold for retrieval evaluation.",
    topic_title="Practice recall and precision with toy retrieval results",
)

ADAPTATION_EVENT = AdaptationEventDTO(
    adaptation_event_id=ADAPTATION_ID,
    goal_id=GOAL_ID,
    curriculum_id=CURRICULUM_ID,
    trigger_type=AdaptationTriggerType.QUIZ_SCORE_BELOW_THRESHOLD,
    trigger_details={"quiz_score": "0.33", "threshold": "0.65"},
    before_summary="The learner reached retrieval metrics before the concept was stable.",
    after_summary="The plan adds focused retrieval metric practice before project integration.",
    changes=[ADAPTATION_CHANGE],
    status=AdaptationStatus.APPLIED,
    quiz_attempt_id=QUIZ_ATTEMPT_ID,
    new_curriculum_id="curriculum_demo_rag_v2",
    created_at=NOW,
    updated_at=NOW,
)

CRITIC_REVIEW = CriticReviewDTO(
    critic_review_id=CRITIC_REVIEW_ID,
    goal_id=GOAL_ID,
    curriculum_id=CURRICULUM_ID,
    run_id=RUN_ID,
    overall_score=0.84,
    pass_status=CriticPassStatus.PASS,
    dimension_scores=CriticDimensionScores(
        coverage=0.86,
        pacing=0.82,
        resource_relevance=0.88,
        assessment_alignment=0.8,
        quiz_readiness=0.82,
    ),
    strengths=["Weak retrieval concepts are addressed before final project integration."],
    issues=["Week 2 needs careful pacing because retrieval metrics are weak."],
    revision_recommendations=[],
    revision_attempt=0,
    created_at=NOW,
    updated_at=NOW,
)

EVALUATION_REPORT = EvaluationReportDTO(
    evaluation_report_id=EVALUATION_REPORT_ID,
    goal_id=GOAL_ID,
    run_id=RUN_ID,
    metric_scores=EvaluationMetricScores(
        curriculum_coverage=0.9,
        difficulty_alignment=0.84,
        pacing_balance=0.82,
        resource_relevance=0.92,
        resource_diversity=0.75,
        quiz_alignment=0.88,
        critic_coherence=0.84,
        workflow_completeness=0.9,
        adaptation_usefulness=0.86,
    ),
    weights={
        "curriculum_coverage": 0.18,
        "difficulty_alignment": 0.12,
        "pacing_balance": 0.1,
        "resource_relevance": 0.14,
        "resource_diversity": 0.08,
        "quiz_alignment": 0.12,
        "critic_coherence": 0.1,
        "adaptation_usefulness": 0.1,
        "workflow_completeness": 0.06,
    },
    overall_score=0.86,
    pass_status=EvaluationPassStatus.PASS,
    warnings=["Fixture data is deterministic and simplified for local validation."],
    recommendations=["Add a larger curated corpus in the dedicated RAG phase."],
    artifact_ids={
        "goal_id": GOAL_ID,
        "knowledge_map_id": KNOWLEDGE_MAP_ID,
        "curriculum_id": CURRICULUM_ID,
        "quiz_attempt_id": QUIZ_ATTEMPT_ID,
    },
    created_at=NOW,
    updated_at=NOW,
)

DASHBOARD_PAYLOAD = DashboardPayload(
    run_summary=RunSummary(
        run_id=RUN_ID,
        status=OrchestrationStatus.COMPLETED,
        mode=ExecutionMode.DEMO,
        current_node="prepare_dashboard_payload",
    ),
    goal_summary=GoalSummary(
        goal_id=GOAL_ID,
        text=CANONICAL_GOAL_TEXT,
        status=GoalStatus.ACTIVE,
    ),
    knowledge_map_summary=KnowledgeMapSummary(
        strong_concepts=KNOWLEDGE_MAP.strong_concepts,
        weak_concepts=KNOWLEDGE_MAP.weak_concepts,
        summary=KNOWLEDGE_MAP.summary,
    ),
    curriculum_summary=CurriculumSummary(
        active_curriculum_id=CURRICULUM_ID,
        title=CURRICULUM.title,
        weeks=[
            CurriculumWeekSummary(
                week_number=week.week_number,
                theme=week.theme,
                topic_titles=[topic.title for topic in week.topics],
            )
            for week in CURRICULUM.weeks
        ],
    ),
    progress_summary=ProgressSummary(
        completion_percentage=25,
        current_topic="Retrieval metrics practice",
        weak_concepts=PROGRESS_STATE.weak_concepts,
    ),
    quiz_summary=QuizSummary(
        latest_score=QUIZ_ATTEMPT.total_score,
        weak_concepts=QUIZ_ATTEMPT.weak_concepts,
    ),
    resources_summary=ResourcesSummary(
        total_attached=len(RESOURCE_ATTACHMENTS),
        average_relevance=0.93,
    ),
    adaptation_summary=AdaptationSummary(recent_events=[ADAPTATION_EVENT.after_summary]),
    evaluation_summary=EvaluationSummary(
        overall_score=EVALUATION_REPORT.overall_score,
        pass_status=EVALUATION_REPORT.pass_status,
    ),
    ui_flags=DashboardUIFlags(show_adaptation_alert=True, requires_user_input=False),
)
