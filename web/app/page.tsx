"use client";

import { FormEvent, useMemo, useState } from "react";

type Moment = {
  id: number;
  time: string;
  title: string;
  text: string;
  tag: string;
  tone: "amber" | "violet" | "mint";
};

const initialMoments: Moment[] = [
  {
    id: 1,
    time: "Today, 6:42 PM",
    title: "Finished the first version of my project",
    text: "I chose forward motion over a perfect result. And it worked.",
    tag: "Growth",
    tone: "amber",
  },
  {
    id: 2,
    time: "Yesterday, 9:15 PM",
    title: "A warm evening with the people I love",
    text: "We left our phones in another room, talked for hours, and laughed a lot.",
    tag: "Relationships",
    tone: "violet",
  },
  {
    id: 3,
    time: "July 28, 10:30 AM",
    title: "Shared my work before it felt perfect",
    text: "I received honest feedback and finally understood what to improve next.",
    tag: "Work",
    tone: "mint",
  },
];

const tagOptions = ["All", "Growth", "Work", "Relationships"];

export default function Home() {
  const [activeTag, setActiveTag] = useState("All");
  const [composerOpen, setComposerOpen] = useState(false);
  const [moments, setMoments] = useState(initialMoments);

  const visibleMoments = useMemo(
    () =>
      activeTag === "All"
        ? moments
        : moments.filter((moment) => moment.tag === activeTag),
    [activeTag, moments],
  );

  const addMoment = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const title = String(form.get("title") || "").trim();
    const text = String(form.get("text") || "").trim();
    const tag = String(form.get("tag") || "Growth");
    if (!title || !text) return;

    setMoments((current) => [
      {
        id: Date.now(),
        time: "Just now",
        title,
        text,
        tag,
        tone: "amber",
      },
      ...current,
    ]);
    setActiveTag("All");
    setComposerOpen(false);
  };

  const scrollToDemo = () =>
    document.getElementById("demo")?.scrollIntoView({ behavior: "smooth" });

  return (
    <main>
      <header className="top-nav">
        <a className="brand" href="#top" aria-label="Chronicle — home">
          <span className="brand-mark">C</span>
          <span>chronicle</span>
        </a>
        <nav aria-label="Main navigation">
          <a href="#possibilities">Features</a>
          <a href="#demo">Live demo</a>
          <a href="#reflection">AI reflections</a>
        </nav>
        <a className="nav-action" href="/app">Open Chronicle</a>
      </header>

      <section className="hero" id="top">
        <div className="hero-orbit orbit-one" aria-hidden="true" />
        <div className="hero-orbit orbit-two" aria-hidden="true" />
        <div className="hero-copy">
          <div className="eyebrow"><span>✦</span> A personal journal for the way you grow</div>
          <h1>
            Keep the <em>moments.</em>
            <br />Notice who you become.
          </h1>
          <p className="hero-lead">
            Chronicle helps you hold on to meaningful moments, move toward your goals,
            and see your progress through thoughtful AI reflections.
          </p>
          <div className="hero-actions">
            <a className="primary-action" href="/app">
              Start your Chronicle <span>→</span>
            </a>
            <button className="secondary-action" onClick={scrollToDemo}>
              Explore the demo
            </button>
          </div>
          <div className="hero-proof">
            <div className="proof-avatars"><span>A</span><span>M</span><span>K</span></div>
            <p><strong>Private by design</strong> · your story stays yours</p>
          </div>
        </div>

        <div className="hero-product" aria-label="Chronicle product preview">
          <div className="product-glow" />
          <div className="floating-note note-one"><span>✦</span> Meaningful moment saved</div>
          <div className="floating-note note-two"><strong>7 days</strong><span>writing streak</span></div>
          <div className="product-window">
            <div className="window-top">
              <span className="mini-brand"><i>C</i> chronicle</span>
              <span className="window-date">August 3</span>
              <span className="mini-avatar">AK</span>
            </div>
            <div className="window-body">
              <p className="window-greeting">Good evening, Alex</p>
              <h2>What would you like to remember today?</h2>
              <button className="quick-entry" onClick={() => setComposerOpen(true)}>
                <span>Capture a thought, a win, or simply a good moment…</span>
                <b>＋</b>
              </button>
              <div className="window-grid">
                <article className="insight-card">
                  <div className="card-label"><span>✦</span> AI insight</div>
                  <p>You notice your progress more often when you record the small wins.</p>
                  <span className="card-link">Open reflection →</span>
                </article>
                <article className="goal-mini">
                  <div className="card-label">Goal of the month</div>
                  <div className="ring"><span>68%</span></div>
                  <strong>Launch my own product</strong>
                  <small>17 of 25 steps</small>
                </article>
              </div>
              <article className="moment-preview">
                <span className="moment-dot amber" />
                <div><small>Today, 6:42 PM · Growth</small><strong>Finished the first version of my project</strong><p>I chose forward motion over a perfect result.</p></div>
              </article>
            </div>
          </div>
        </div>
      </section>

      <section className="feature-section" id="possibilities">
        <div className="section-heading centered-heading">
          <span className="section-kicker">One day at a time</span>
          <h2>Do more than save memories.<br /><em>Understand yourself.</em></h2>
          <p>Chronicle turns scattered entries into a clear picture of how you are moving forward.</p>
        </div>
        <div className="features-grid">
          <article className="feature-card feature-large">
            <span className="feature-index">01</span>
            <div className="feature-visual timeline-visual"><i /><i /><i /></div>
            <h3>Moments worth returning to</h3>
            <p>Capture an experience in seconds, organize it by area of life, and find it whenever you need it.</p>
          </article>
          <article className="feature-card">
            <span className="feature-index">02</span>
            <div className="feature-visual goal-visual"><span>74%</span></div>
            <h3>Goals grounded in real life</h3>
            <p>Connect everyday actions to your goals and notice the progress that is easy to overlook.</p>
          </article>
          <article className="feature-card dark-feature" id="reflection">
            <span className="feature-index">03</span>
            <div className="feature-visual stars-visual">✦ <small>✧</small> ✦</div>
            <h3>AI that listens</h3>
            <p>No judgment and no loud advice. Just thoughtful observations drawn from your own story.</p>
          </article>
        </div>
      </section>

      <section className="demo-section" id="demo">
        <div className="section-heading demo-heading">
          <div>
            <span className="section-kicker">Interactive preview</span>
            <h2>Your story —<br /><em>all in one place.</em></h2>
          </div>
          <p>Choose an area of life or add a new moment. The experience works right here on the page.</p>
        </div>

        <div className="journal-shell">
          <aside className="journal-sidebar">
            <a className="brand compact-brand" href="#top"><span className="brand-mark">C</span><span>chronicle</span></a>
            <div className="sidebar-nav">
              <button className="active"><span>◉</span>Today</button>
              <button><span>◌</span>Moments</button>
              <button><span>◇</span>Goals</button>
              <button><span>✦</span>Reflections</button>
            </div>
            <div className="sidebar-spacer" />
            <div className="streak-card"><span>7</span><div><strong>day streak</strong><small>Keep it going</small></div></div>
            <button className="profile-button"><span>AK</span><div><strong>Alex</strong><small>Settings</small></div></button>
          </aside>

          <div className="journal-content">
            <header className="journal-header">
              <div><span className="date-label">SUNDAY, AUGUST 3</span><h3>Good evening, Alex</h3></div>
              <button className="add-button" onClick={() => setComposerOpen(true)}>＋ New moment</button>
            </header>

            <div className="journal-columns">
              <section className="timeline-column">
                <div className="filter-row">
                  {tagOptions.map((tag) => (
                    <button key={tag} className={activeTag === tag ? "active" : ""} onClick={() => setActiveTag(tag)}>{tag}</button>
                  ))}
                </div>
                <div className="timeline-list">
                  {visibleMoments.map((moment) => (
                    <article className="timeline-item" key={moment.id}>
                      <span className={`moment-dot ${moment.tone}`} />
                      <div className="timeline-card">
                        <div className="timeline-meta"><span>{moment.time}</span><span>{moment.tag}</span></div>
                        <h4>{moment.title}</h4>
                        <p>{moment.text}</p>
                        <button aria-label={`Add ${moment.title} to favorites`}>♡</button>
                      </div>
                    </article>
                  ))}
                </div>
              </section>

              <aside className="reflection-column">
                <article className="reflection-card">
                  <div className="reflection-top"><span>✦</span><small>YOUR WEEK</small></div>
                  <h4>You are choosing action over waiting more often.</h4>
                  <p>Courage appears across four entries this week: you shared your work, asked for feedback, and finished what you started.</p>
                  <button>Read your reflection <span>→</span></button>
                </article>
                <article className="progress-card">
                  <div className="progress-head"><div><small>GOAL OF THE MONTH</small><h4>Launch my own product</h4></div><strong>68%</strong></div>
                  <div className="progress-track"><i /></div>
                  <div className="progress-meta"><span>17 steps completed</span><span>8 remaining</span></div>
                </article>
                <blockquote>“We do not remember days.<br />We remember moments.”<cite>— Cesare Pavese</cite></blockquote>
              </aside>
            </div>
          </div>
        </div>
      </section>

      <section className="closing-section">
        <span className="closing-star">✦</span>
        <h2>Your story is already unfolding.</h2>
        <p>Start noticing it today.</p>
        <a className="primary-action" href="/app">Open Chronicle <span>→</span></a>
      </section>

      <footer>
        <a className="brand" href="#top"><span className="brand-mark">C</span><span>chronicle</span></a>
        <p>A personal journal for moments, goals, and honest reflection.</p>
        <span>Made with care · 2026</span>
      </footer>

      {composerOpen && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setComposerOpen(false)}>
          <div className="composer" role="dialog" aria-modal="true" aria-labelledby="composer-title" onMouseDown={(event) => event.stopPropagation()}>
            <button className="modal-close" onClick={() => setComposerOpen(false)} aria-label="Close">×</button>
            <span className="section-kicker">New moment</span>
            <h2 id="composer-title">What would you like to remember?</h2>
            <form onSubmit={addMoment}>
              <label>Title<input name="title" placeholder="For example, I took the first meaningful step" autoFocus required /></label>
              <label>Details<textarea name="text" placeholder="What happened, and why does it matter to you?" rows={4} required /></label>
              <label>Area of life<select name="tag" defaultValue="Growth"><option>Growth</option><option>Work</option><option>Relationships</option></select></label>
              <button className="primary-action" type="submit">Save moment <span>→</span></button>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
