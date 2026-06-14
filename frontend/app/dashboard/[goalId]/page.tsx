import type { CSSProperties } from "react";

import { WeekTimeline } from "@/components/curriculum/WeekTimeline";
import {
  CurriculumApiError,
  getCurriculum,
  getExampleCurriculum,
  type CurriculumPlan
} from "@/lib/api/curriculum";

type DashboardPageProps = {
  params: {
    goalId: string;
  };
};

export default async function CurriculumDashboardPage({ params }: DashboardPageProps) {
  const requestedId = decodeURIComponent(params.goalId);
  const result = await loadCurriculum(requestedId);

  if (!result.curriculum) {
    return (
      <main style={pageStyle}>
        <section style={heroStyle}>
          <p style={eyebrowStyle}>Curriculum</p>
          <h1 style={headingStyle}>No curriculum available</h1>
          <p style={supportingStyle}>{result.error}</p>
        </section>
        <section style={noticeStyle}>
          Backend curriculum storage is currently in-memory for Phase 5. Restarting the
          backend clears generated curricula until MongoDB persistence is added.
        </section>
      </main>
    );
  }

  const { curriculum } = result;

  return (
    <main style={pageStyle}>
      <section style={heroStyle}>
        <p style={eyebrowStyle}>Curriculum</p>
        <h1 style={headingStyle}>{curriculum.goal}</h1>
        <div style={summaryGridStyle}>
          <Metric label="Timeline" value={`${curriculum.timeline_weeks} weeks`} />
          <Metric label="Weekly time" value={`${curriculum.hours_per_week}h`} />
          <Metric label="Total estimate" value={`${curriculum.total_hours.toFixed(1)}h`} />
          <Metric label="Level" value={curriculum.difficulty_progression.ending_level} />
        </div>
      </section>

      <section style={knowledgeStyle}>
        <KnowledgeColumn title="Strong" items={curriculum.knowledge_map.strong} tone="strong" />
        <KnowledgeColumn title="Weak" items={curriculum.knowledge_map.weak} tone="weak" />
        <KnowledgeColumn title="Missing" items={curriculum.knowledge_map.missing} tone="missing" />
      </section>

      {curriculum.validation_issues.length > 0 ? (
        <section style={warningStyle}>
          {curriculum.validation_issues.map((issue) => (
            <p key={`${issue.code}-${issue.week_number ?? "plan"}`} style={warningTextStyle}>
              {issue.severity}: {issue.message}
            </p>
          ))}
        </section>
      ) : null}

      <WeekTimeline weeks={curriculum.weeks} />

      <section style={notesStyle}>
        <h2 style={sectionTitleStyle}>Generation notes</h2>
        <ul style={noteListStyle}>
          {curriculum.generation_notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
        <p style={temporaryStorageStyle}>
          Temporary Phase 5 storage is in-memory; generated curricula disappear when the
          backend restarts.
        </p>
      </section>
    </main>
  );
}

async function loadCurriculum(
  requestedId: string
): Promise<{ curriculum: CurriculumPlan | null; error: string | null }> {
  try {
    if (requestedId === "demo") {
      const example = await getExampleCurriculum();
      return { curriculum: example.curriculum, error: null };
    }

    return { curriculum: await getCurriculum(requestedId), error: null };
  } catch (error) {
    if (error instanceof CurriculumApiError) {
      return {
        curriculum: null,
        error: `${error.message} (${error.status}${error.code ? `, ${error.code}` : ""}).`
      };
    }

    return {
      curriculum: null,
      error: "The frontend could not reach the PathAI backend curriculum API."
    };
  }
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div style={metricStyle}>
      <span style={metricLabelStyle}>{label}</span>
      <strong style={metricValueStyle}>{value}</strong>
    </div>
  );
}

function KnowledgeColumn({
  title,
  items,
  tone
}: {
  title: string;
  items: string[];
  tone: "strong" | "weak" | "missing";
}) {
  const accent = tone === "strong" ? "#15803d" : tone === "weak" ? "#b45309" : "#b91c1c";
  return (
    <section style={knowledgeColumnStyle}>
      <h2 style={{ ...sectionTitleStyle, color: accent }}>{title}</h2>
      <div style={tagRowStyle}>
        {items.length > 0 ? (
          items.map((item) => (
            <span key={item} style={{ ...knowledgeTagStyle, borderColor: accent }}>
              {item}
            </span>
          ))
        ) : (
          <span style={emptyTagStyle}>None recorded</span>
        )}
      </div>
    </section>
  );
}

const pageStyle: CSSProperties = {
  minHeight: "100vh",
  margin: 0,
  padding: "32px clamp(16px, 4vw, 56px)",
  backgroundColor: "#f6f8fb",
  color: "#101828",
  fontFamily:
    'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
};

const heroStyle: CSSProperties = {
  maxWidth: 1120,
  margin: "0 auto 24px"
};

const eyebrowStyle: CSSProperties = {
  margin: 0,
  color: "#1570ef",
  fontSize: 13,
  fontWeight: 800,
  textTransform: "uppercase"
};

const headingStyle: CSSProperties = {
  margin: "8px 0 18px",
  fontSize: 40,
  lineHeight: 1.12,
  color: "#101828"
};

const supportingStyle: CSSProperties = {
  margin: 0,
  maxWidth: 760,
  color: "#475467",
  lineHeight: 1.55
};

const summaryGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
  gap: 12
};

const metricStyle: CSSProperties = {
  border: "1px solid #dbe3ef",
  borderRadius: 8,
  padding: 14,
  backgroundColor: "#ffffff"
};

const metricLabelStyle: CSSProperties = {
  display: "block",
  color: "#667085",
  fontSize: 13
};

const metricValueStyle: CSSProperties = {
  display: "block",
  marginTop: 4,
  color: "#101828",
  fontSize: 20
};

const knowledgeStyle: CSSProperties = {
  maxWidth: 1120,
  margin: "0 auto 24px",
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: 12
};

const knowledgeColumnStyle: CSSProperties = {
  border: "1px solid #dbe3ef",
  borderRadius: 8,
  padding: 16,
  backgroundColor: "#ffffff"
};

const sectionTitleStyle: CSSProperties = {
  margin: "0 0 10px",
  fontSize: 18,
  lineHeight: 1.3
};

const tagRowStyle: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: 8
};

const knowledgeTagStyle: CSSProperties = {
  border: "1px solid",
  borderRadius: 999,
  padding: "5px 10px",
  color: "#344054",
  backgroundColor: "#ffffff",
  fontSize: 13,
  fontWeight: 600
};

const emptyTagStyle: CSSProperties = {
  color: "#667085",
  fontSize: 14
};

const warningStyle: CSSProperties = {
  maxWidth: 1120,
  margin: "0 auto 24px",
  border: "1px solid #fed7aa",
  borderRadius: 8,
  padding: 16,
  backgroundColor: "#fff7ed"
};

const warningTextStyle: CSSProperties = {
  margin: 0,
  color: "#9a3412"
};

const notesStyle: CSSProperties = {
  maxWidth: 1120,
  margin: "24px auto 0",
  border: "1px solid #dbe3ef",
  borderRadius: 8,
  padding: 20,
  backgroundColor: "#ffffff"
};

const noteListStyle: CSSProperties = {
  margin: 0,
  paddingLeft: 20,
  color: "#344054",
  lineHeight: 1.6
};

const temporaryStorageStyle: CSSProperties = {
  margin: "14px 0 0",
  color: "#667085",
  fontSize: 14
};

const noticeStyle: CSSProperties = {
  maxWidth: 1120,
  margin: "0 auto",
  border: "1px solid #dbe3ef",
  borderRadius: 8,
  padding: 16,
  backgroundColor: "#ffffff",
  color: "#475467"
};
