export default function CurriculumDashboardLoading() {
  return (
    <main
      style={{
        minHeight: "100vh",
        padding: "32px clamp(16px, 4vw, 56px)",
        backgroundColor: "#f6f8fb",
        color: "#101828",
        fontFamily:
          'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
      }}
    >
      <section
        style={{
          maxWidth: 1120,
          margin: "0 auto",
          border: "1px solid #dbe3ef",
          borderRadius: 8,
          padding: 20,
          backgroundColor: "#ffffff"
        }}
      >
        <p style={{ margin: 0, color: "#1570ef", fontSize: 13, fontWeight: 800 }}>
          Curriculum
        </p>
        <h1 style={{ margin: "8px 0 10px", fontSize: 32 }}>Loading curriculum</h1>
        <p style={{ margin: 0, color: "#475467" }}>
          Preparing the week-by-week plan from the backend API.
        </p>
      </section>
    </main>
  );
}
