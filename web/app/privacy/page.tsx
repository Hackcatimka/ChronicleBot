const sections = [
  ["What Chronicle stores", "Chronicle stores the profile name and preferences you provide, your journal moments, goals, progress, selected life areas, and links between moments and goals."],
  ["Why the data is used", "This information is used only to provide the journal, calculate your personal progress views, restore your entries, and apply the settings you choose."],
  ["Sharing and selling", "Chronicle does not sell your personal data. The current product does not share journal content with advertisers or unrelated third parties."],
  ["Storage and security", "Journal data is stored in Chronicle's application database. Reasonable technical safeguards are used, but no online service can guarantee absolute security."],
  ["Your controls", "You can export your journal from Settings, delete all moments and goals while keeping your profile, or permanently delete the account and all associated data."],
  ["Retention", "Data remains available until you remove it. Account deletion permanently erases the profile, preferences, moments, goals, and their relationships from the active application database."],
  ["Changes to this policy", "If Chronicle's data practices materially change, this page will be updated before the new practices apply."],
  ["Contact", "For privacy questions, contact the Chronicle project owner through the public project repository."],
] as const;

export default function PrivacyPage() {
  return <main className="privacy-page">
    <nav><a className="privacy-brand" href="/"><span>C</span><strong>chronicle</strong></a><a href="/app">Back to Chronicle →</a></nav>
    <article>
      <header><small>PRIVACY · LAST UPDATED AUGUST 7, 2026</small><h1>Your story belongs to you.</h1><p>This policy explains what Chronicle stores and the controls available to you. Chronicle is currently an early-stage personal journal product.</p></header>
      <div className="privacy-summary"><span>01</span><p>Your journal is used to provide Chronicle.</p><span>02</span><p>Your personal data is not sold.</p><span>03</span><p>You can export or permanently erase your data.</p></div>
      <section>{sections.map(([title, body]) => <div key={title}><h2>{title}</h2><p>{body}</p></div>)}</section>
      <aside><h2>Кратко на русском</h2><p>Chronicle хранит имя и настройки профиля, выбранные сферы жизни, записи дневника, цели и прогресс. Эти данные используются только для работы приложения и не продаются рекламодателям. В настройках можно экспортировать дневник, удалить записи и цели или полностью удалить аккаунт со всеми связанными данными.</p></aside>
    </article>
    <footer><a href="/app">← Return to your Chronicle</a><span>Chronicle · Personal journal</span></footer>
  </main>;
}
