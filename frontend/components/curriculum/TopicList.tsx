import type { CSSProperties } from "react";

import type { CurriculumTopic, TopicPriority } from "@/lib/api/curriculum";

type TopicListProps = {
  topics: CurriculumTopic[];
};

const priorityStyles: Record<TopicPriority, CSSProperties> = {
  high: { backgroundColor: "#fee2e2", color: "#991b1b", borderColor: "#fecaca" },
  medium: { backgroundColor: "#fef3c7", color: "#92400e", borderColor: "#fde68a" },
  low: { backgroundColor: "#dcfce7", color: "#166534", borderColor: "#bbf7d0" }
};

export function TopicList({ topics }: TopicListProps) {
  return (
    <div style={listStyle}>
      {topics.map((topic) => (
        <article key={topic.topic_id} style={topicStyle}>
          <div style={topicHeaderStyle}>
            <div>
              <h4 style={topicTitleStyle}>{topic.title}</h4>
              <p style={topicMetaStyle}>
                {topic.estimated_hours.toFixed(1)}h - {topic.difficulty}
              </p>
            </div>
            <span style={{ ...badgeStyle, ...priorityStyles[topic.priority] }}>
              {topic.priority}
            </span>
          </div>

          <p style={rationaleStyle}>{topic.rationale}</p>

          {topic.prerequisites.length > 0 ? (
            <div style={tagRowStyle}>
              {topic.prerequisites.map((prerequisite) => (
                <span key={prerequisite} style={tagStyle}>
                  {prerequisite}
                </span>
              ))}
            </div>
          ) : null}

          <div style={subtopicGridStyle}>
            {topic.subtopics.map((subtopic) => (
              <section key={subtopic.title} style={subtopicStyle}>
                <div style={subtopicHeaderStyle}>
                  <strong>{subtopic.title}</strong>
                  <span>{subtopic.estimated_hours.toFixed(1)}h</span>
                </div>
                <p style={subtopicTextStyle}>{subtopic.learning_outcome}</p>
              </section>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}

const listStyle: CSSProperties = {
  display: "grid",
  gap: 12
};

const topicStyle: CSSProperties = {
  border: "1px solid #dbe3ef",
  borderRadius: 8,
  padding: 16,
  backgroundColor: "#ffffff"
};

const topicHeaderStyle: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  gap: 12,
  alignItems: "flex-start"
};

const topicTitleStyle: CSSProperties = {
  margin: 0,
  fontSize: 18,
  lineHeight: 1.3,
  color: "#172033"
};

const topicMetaStyle: CSSProperties = {
  margin: "4px 0 0",
  color: "#667085",
  fontSize: 14
};

const badgeStyle: CSSProperties = {
  border: "1px solid",
  borderRadius: 999,
  padding: "4px 10px",
  fontSize: 12,
  fontWeight: 700,
  textTransform: "uppercase",
  whiteSpace: "nowrap"
};

const rationaleStyle: CSSProperties = {
  margin: "12px 0",
  color: "#344054",
  lineHeight: 1.5
};

const tagRowStyle: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: 8,
  marginBottom: 12
};

const tagStyle: CSSProperties = {
  backgroundColor: "#eef4ff",
  color: "#3538cd",
  borderRadius: 999,
  padding: "4px 9px",
  fontSize: 12,
  fontWeight: 600
};

const subtopicGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: 10
};

const subtopicStyle: CSSProperties = {
  border: "1px solid #edf1f7",
  borderRadius: 8,
  padding: 12,
  backgroundColor: "#f8fafc"
};

const subtopicHeaderStyle: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  gap: 12,
  color: "#172033",
  fontSize: 14
};

const subtopicTextStyle: CSSProperties = {
  margin: "8px 0 0",
  color: "#475467",
  fontSize: 14,
  lineHeight: 1.45
};
