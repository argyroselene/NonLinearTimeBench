function passageFromStory(story) {
  const byId = Object.fromEntries(story.events.map((e) => [e.id, e]))
  const orderedIds = Object.keys(byId).sort((a, b) => Number(a.slice(1)) - Number(b.slice(1)))
  return orderedIds.map((id) => byId[id])
}

export default function PassagePanel({ story, selectedNode, onSelectNode, scoreById }) {
  const passage = passageFromStory(story)

  return (
    <div className="passage-panel">
      <h2>Shuffled passage</h2>
      <ol>
        {passage.map((event) => {
          const score = scoreById?.[event.id]
          return (
            <li
              key={event.id}
              className={event.id === selectedNode ? 'selected' : ''}
              onClick={() => onSelectNode(event.id)}
            >
              <span className="sentence-id">{event.id}</span>
              <span className="sentence-thread">[{event.thread_id}]</span>
              {event.text}
              {score !== undefined && (
                <span className={`score-badge ${score < 0.5 ? 'low' : score < 1 ? 'mid' : 'high'}`}>
                  {score.toFixed(2)}
                </span>
              )}
            </li>
          )
        })}
      </ol>
    </div>
  )
}
