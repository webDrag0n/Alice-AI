# Memory System Architecture

The Alice AI memory system is designed to mimic human cognitive processes, divided into three distinct tiers: **Short-Term**, **Long-Term**, and **Consolidated (Solidified)**.

## 1. Short-Term Memory (Working Memory)

This is the agent's "Stream of Consciousness". It is transient, limited in capacity, and exists primarily in RAM during the runtime.

### Composition
- **Perception Buffer**: A raw buffer that temporarily holds sensory inputs (user messages, system events, action results) before processing.
- **Instant Memory**: A FIFO queue (size ~10) containing summarized perceptions. This represents what the agent is "currently thinking about".
- **Context Window**: The recent conversation history (User/Assistant messages) fed directly into the LLM's context.

### Mechanism
- **Update**: Automatically updated by the `Observe` node in every cycle.
- **Retrieval**: Directly injected into the `Think` node's prompt.
- **Loss**: Information here is lost if the process restarts, unless it has been promoted to Long-Term Memory.

---

## 2. Long-Term Memory

This tier stores information that persists across sessions. It is divided into four categories based on content type and storage medium. Note that while most are stored in the Vector Database (Weaviate), **Actions** are stored as executable code.

### A. Episodic Memory (Experiences)
Records specific events, conversations, and experiences.

- **Storage**: Weaviate Vector DB (`type="episodic"`).
- **Composition**: Content text, Timestamp, Importance score, User ID.
- **Update**: 
    - **Trigger**: Explicitly via the `Memorize` action, or implicitly when a `ThinkComplete` action summarizes a thought chain.
    - **Process**: The content is embedded (vectorized) and stored.
- **Retrieval**: 
    - **Trigger**: `Recall` (precise search) or `Associate` (fuzzy/creative search) actions.
    - **Mechanism**: Vector similarity search against the current context or query.

### B. Beliefs (Semantic/Cognitive)
Stores facts, world knowledge, and formed opinions.

- **Storage**: Weaviate Vector DB (`type="cognitive"`).
- **Composition**: Content (The belief), Tags (e.g., "physics", "user_preference"), Confidence level.
- **Update**: 
    - **Trigger**: `AddBelief` action.
    - **Process**: Stored with high importance to ensure better retrieval.
- **Retrieval**: Same as Episodic (Vector Search).

### C. Social Memory (Relationships)
Tracks the evolving relationship with the user.

- **Storage**: Weaviate Vector DB (`type="social_state"`).
- **Composition**: 
    - **Metrics**: Intimacy (0-100), Trust (0-100).
    - **Stage**: Relationship label (e.g., "Stranger", "Friend", "Partner").
    - **Summary**: A qualitative description of the relationship dynamic.
- **Update**: 
    - **Trigger**: `UpdateRelationship` action.
    - **Process**: A new snapshot of the social state is appended to the DB.
- **Retrieval**: 
    - **Trigger**: Automatically fetched at the start of every `Think` cycle.
    - **Mechanism**: Query for the latest entry with `type="social_state"`.

### D. Actions (Procedural Memory)
Stores "how to do things". Unlike other memories, these are executable skills.

- **Storage**: **File System** (Python Code).
- **Composition**: 
    - **Innate**: Hardcoded classes in `soul/actions/innate.py`.
    - **Learned**: Dynamically generated Python classes in `soul/actions/learned.py`.
- **Update**: 
    - **Trigger**: `LearnSkill` action.
    - **Process**: The agent writes new Python code to define a new `Action` class and reloads the registry.
- **Retrieval**: 
    - **Mechanism**: The `ActionRegistry` loads all available action classes at startup. The `Think` node receives a list of available tools (signatures and descriptions) in its prompt.

---

## 3. Consolidated Memory (Metacognition)

This represents the agent's "Instincts" and "Methodology". These are deep-seated, immutable logic patterns that define *how* the agent thinks, rather than *what* it knows.

### Composition
- **Mental Models**: Fundamental principles (e.g., "First Principles Thinking", "OODA Loop").
- **Strategies**: Heuristics for tool use and problem-solving.
- **Self-Reflection**: Rules for managing internal state and emotions.

### Mechanism
- **Storage**: Hardcoded Python List in `soul/memory/metacognition.py`.
- **Update**: Currently read-only for the agent (Developer managed). In the future, this could be updated via a "Deep Sleep" optimization process.
- **Retrieval**: 
    - **Mechanism**: These are **always** injected into the System Prompt of the `Think` node. They act as the "operating system" instructions for the LLM.

---

## Summary Table

| Memory Type | Category | Storage Medium | Update Method | Retrieval Method |
| :--- | :--- | :--- | :--- | :--- |
| **Working** | Short-Term | RAM | `Observe` Loop | Prompt Context |
| **Episodic** | Long-Term | Weaviate | `Memorize` / `ThinkComplete` | `Recall` / `Associate` |
| **Beliefs** | Long-Term | Weaviate | `AddBelief` | `Recall` / `Associate` |
| **Social** | Long-Term | Weaviate | `UpdateRelationship` | Auto-fetch (Latest) |
| **Actions** | Long-Term | Code Files | `LearnSkill` (Code Gen) | `ActionRegistry` |
| **Metacognition** | Consolidated | Code (Static) | Developer / Deep Sleep | System Prompt Injection |
