import type { CSSProperties } from "react";

import { TopicList } from "@/components/curriculum/TopicList";
import type { CurriculumWeek } from "@/lib/api/curriculum";

type WeekTimelineProps = {
  weeks: CurriculumWeek[];
};

export function WeekTimeline({ weeks }: WeekTimelineProps) {
  return (
    <ol style={timelineStyle}>
      {weeks.map((week) => (
        <li key={week.week_number} style={weekItemStyle}>
          <div style={railStyle}>
            <span style={dotStyle}>{week.week_number}</span>
          </div>
          <article style={weekPanelStyle}>
            <header style={weekHeaderStyle}>
              <div>
                <p style={eyebrowStyle}>Week {week.week_number}</p>
                <h3 style={titleStyle}>{week.theme}</h3>
              </div>
              <div style={weekStatsStyle}>
                <span>{week.estimated_hours.toFixed(1)}h</span>
                <span>{week.difficulty}</span>
                {week.project_or_application ? <span>Project</span> : null}
              </div>
            </header>

            <p style={goalStyle}>{week.weekly_goal}</p>

            <section style={milestoneStyle}>
              <strong>{week.milestone.title}</strong>
              <p>{week.milestone.description}</p>
              <span>{week.milestone.deliverable}</span>
            </section>

            <TopicList topics={week.topics} />
          </article>
        </li>
      ))}
    </ol>
  );
}

const timelineStyle: CSSProperties = {
  listStyle: "none",
  margin: 0,
  padding: 0,
  display: "grid",
  gap: 18
};

const weekItemStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "44px minmax(0, 1fr)",
  gap: 12
};

const railStyle: CSSProperties = {
  display: "flex",
  justifyContent: "center",
  position: "relative"
};

const dotStyle: CSSProperties = {
  width: 34,
  height: 34,
  borderRadius: "50%",
  backgroundColor: "#14532d",
  color: "#ffffff",
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  fontWeight: 800,
  marginTop: 20
};

const weekPanelStyle: CSSProperties = {
  border: "1px solid #dbe3ef",
  borderRadius: 8,
  padding: 20,
  backgroundColor: "#ffffff",
  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.05)"
};

const weekHeaderStyle: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  gap: 16,
  alignItems: "flex-start",
  flexWrap: "wrap"
};

const eyebrowStyle: CSSProperties = {
  margin: 0,
  color: "#1570ef",
  fontSize: 13,
  fontWeight: 800,
  textTransform: "uppercase"
};

const titleStyle: CSSProperties = {
  margin: "4px 0 0",
  color: "#101828",
  fontSize: 24,
  lineHeight: 1.25
};

const weekStatsStyle: CSSProperties = {
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
  justifyContent: "flex-end",
  color: "#344054",
  fontSize: 13,
  fontWeight: 700
};

const goalStyle: CSSProperties = {
  margin: "14px 0",
  color: "#344054",
  lineHeight: 1.55
};

const milestoneStyle: CSSProperties = {
  borderLeft: "4px solid #1570ef",
  backgroundColor: "#eff6ff",
  borderRadius: 8,
  padding: 14,
  marginBottom: 14,
  color: "#1d2939"
};
