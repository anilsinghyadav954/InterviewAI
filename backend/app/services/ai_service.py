import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from bson import ObjectId
import requests
from fastapi import HTTPException, status

from app.config import settings
from app.database import (
    get_interview_question_sets_collection,
    get_resume_analyses_collection,
    get_interview_evaluations_collection,
)

logger = logging.getLogger(__name__)

# ==============================================================================
# Comprehensive Domain Question Bank for All 8 Target Roles
# ==============================================================================
FALLBACK_QUESTIONS_DB: Dict[str, Dict[str, Dict[str, List[Dict[str, Any]]]]] = {
    "Software Developer": {
        "Technical": {
            "Beginner": [
                {
                    "question": "What is the difference between an Array and a Linked List, and when would you choose one over the other?",
                    "category": "Coding",
                    "topic": "Data Structures",
                    "expected_focus": ["Contiguous memory vs pointer overhead", "O(1) random access vs O(n) traversal", "Insertion and deletion complexities"],
                },
                {
                    "question": "Explain the four core principles of Object-Oriented Programming (OOP) with real-world software examples.",
                    "category": "Programming",
                    "topic": "OOP Principles",
                    "expected_focus": ["Encapsulation", "Abstraction", "Inheritance", "Polymorphism"],
                },
                {
                    "question": "What is the difference between synchronous and asynchronous execution in modern programming languages?",
                    "category": "Technical",
                    "topic": "Concurrency Basics",
                    "expected_focus": ["Blocking vs non-blocking I/O", "Event loop and thread pools", "User experience responsiveness"],
                },
                {
                    "question": "Explain how version control branching works in Git, and describe how you resolve merge conflicts.",
                    "category": "Technical",
                    "topic": "Git & Version Control",
                    "expected_focus": ["Feature branches vs main", "Conflict markers (<<< === >>>)", "Rebase vs merge tradeoffs"],
                },
                {
                    "question": "What are unit tests, integration tests, and end-to-end tests, and why is test-driven development valuable?",
                    "category": "Problem Solving",
                    "topic": "Software Testing",
                    "expected_focus": ["Test pyramid concept", "Isolation and mocking", "Preventing regressions"],
                },
            ],
            "Intermediate": [
                {
                    "question": "How do hash maps resolve collisions under the hood, and how can collision spikes affect time complexity?",
                    "category": "Coding",
                    "topic": "Hash Tables & Algorithms",
                    "expected_focus": ["Chaining vs open addressing", "Hash functions and distribution", "Worst case degradation to O(n)"],
                },
                {
                    "question": "Explain the SOLID design principles and how following them improves code maintainability in team environments.",
                    "category": "Programming",
                    "topic": "Software Architecture",
                    "expected_focus": ["Single Responsibility", "Open/Closed", "Liskov Substitution", "Interface Segregation", "Dependency Inversion"],
                },
                {
                    "question": "Describe how you diagnose and resolve a severe memory leak in a long-running software application.",
                    "category": "Problem Solving",
                    "topic": "Debugging & Diagnostics",
                    "expected_focus": ["Memory profiling tools & heap dumps", "Uncollected event listeners / circular references", "Reproducing in staging"],
                },
                {
                    "question": "What is the difference between process-based concurrency and thread-based concurrency?",
                    "category": "Technical",
                    "topic": "Operating Systems & Concurrency",
                    "expected_focus": ["Shared memory vs isolated address space", "Context switching overhead", "Race conditions and synchronization locks"],
                },
                {
                    "question": "How do you design RESTful API endpoints for pagination, filtering, and sorting over large datasets?",
                    "category": "System Design",
                    "topic": "API Design",
                    "expected_focus": ["Offset vs cursor-based pagination", "Query parameter conventions", "Database index alignment"],
                },
            ],
            "Advanced": [
                {
                    "question": "How do you design a distributed locking mechanism to prevent double-spending or duplicate job processing across multiple microservices?",
                    "category": "System Design",
                    "topic": "Distributed Systems",
                    "expected_focus": ["Redis Redlock / Zookeeper recipes", "TTL expiry and fencing tokens", "Network partition failure modes"],
                },
                {
                    "question": "Explain the CAP theorem and describe how modern distributed databases (e.g. Cassandra vs CockroachDB) make tradeoffs.",
                    "category": "System Design",
                    "topic": "Distributed Data Consistency",
                    "expected_focus": ["Consistency vs Availability under Partition", "PACELC extension", "Eventual consistency vs 2PC consensus"],
                },
                {
                    "question": "How would you architect a fault-tolerant message queue consumer group that guarantees exactly-once processing semantics?",
                    "category": "System Design",
                    "topic": "Event-Driven Architecture",
                    "expected_focus": ["Idempotency keys & deduplication tables", "Consumer offset commits", "Dead-letter queues with exponential backoff"],
                },
                {
                    "question": "How do CPU caches (L1/L2/L3) and cache-line false sharing impact the performance of high-throughput multithreaded code?",
                    "category": "Technical",
                    "topic": "Low-Level Performance",
                    "expected_focus": ["Spatial and temporal locality", "Cache line invalidation", "Memory barriers and atomic instructions"],
                },
                {
                    "question": "How do you execute zero-downtime database schema migrations for tables with hundreds of millions of records?",
                    "category": "Database",
                    "topic": "Database Architecture",
                    "expected_focus": ["Expand and contract pattern", "Online schema change tools (gh-ost / pt-online-schema-change)", "Backward-compatible code deployment"],
                },
            ],
        },
    },
    "Frontend Developer": {
        "Technical": {
            "Beginner": [
                {
                    "question": "Explain the difference between HTML semantics, inline elements, and block elements with practical examples.",
                    "category": "Web Development",
                    "topic": "HTML Semantics",
                    "expected_focus": ["header/nav/section/article accessibility", "div vs span display properties", "SEO benefits"],
                },
                {
                    "question": "What is the CSS Box Model, and how does 'box-sizing: border-box' change margin and padding calculations?",
                    "category": "Web Development",
                    "topic": "CSS Fundamentals",
                    "expected_focus": ["Content, padding, border, margin", "border-box vs content-box calculation", "Layout overflow prevention"],
                },
                {
                    "question": "Explain the difference between let, const, and var in modern JavaScript with regard to scoping and hoisting.",
                    "category": "Programming",
                    "topic": "JavaScript Fundamentals",
                    "expected_focus": ["Block scope vs function scope", "Temporal Dead Zone (TDZ)", "Immutability of const references"],
                },
                {
                    "question": "What is the Virtual DOM in React, and how does React determine which elements need to be updated?",
                    "category": "Web Development",
                    "topic": "React Mechanics",
                    "expected_focus": ["In-memory UI representation", "Diffing reconciliation algorithm", "Keys in lists"],
                },
                {
                    "question": "How do you make a web page responsive using CSS Flexbox, Grid, and Media Queries?",
                    "category": "Web Development",
                    "topic": "Responsive Design",
                    "expected_focus": ["Flexbox 1D vs Grid 2D layout", "Mobile-first media query breakpoints", "Fluid units (rem, %, vh/vw)"],
                },
            ],
            "Intermediate": [
                {
                    "question": "Explain the JavaScript Event Loop, Call Stack, Microtask Queue (Promises), and Macrotask Queue (setTimeout).",
                    "category": "Programming",
                    "topic": "JS Concurrency & Event Loop",
                    "expected_focus": ["Execution order prioritization", "requestAnimationFrame timing", "UI thread freezing prevention"],
                },
                {
                    "question": "Compare React state management options: useState/useReducer, Context API, and global stores like Zustand or Redux Toolkit.",
                    "category": "Web Development",
                    "topic": "State Management Architecture",
                    "expected_focus": ["Prop drilling mitigation", "Context re-render performance bottlenecks", "Selective subscriptions"],
                },
                {
                    "question": "What are Core Web Vitals (LCP, FID/INP, CLS) and what concrete frontend optimizations improve each metric?",
                    "category": "Web Development",
                    "topic": "Web Performance Optimization",
                    "expected_focus": ["Largest Contentful Paint image optimization", "Interaction to Next Paint main-thread delays", "Cumulative Layout Shift dimension reservation"],
                },
                {
                    "question": "How do you protect a modern client-side application against Cross-Site Scripting (XSS) and Cross-Site Request Forgery (CSRF)?",
                    "category": "Technical",
                    "topic": "Frontend Security",
                    "expected_focus": ["Sanitizing user-generated HTML", "HttpOnly SameSite cookies", "Content Security Policy (CSP) headers"],
                },
                {
                    "question": "How do React custom hooks encapsulate reusable logic, and what rules must be followed when creating them?",
                    "category": "Coding",
                    "topic": "React Custom Hooks",
                    "expected_focus": ["Only call at top level", "Encapsulating side-effects with cleanup", "Dependency array correctness"],
                },
            ],
            "Advanced": [
                {
                    "question": "Deep dive into React 18+ Fiber architecture, Concurrent Mode, and how useTransition prioritizes UI rendering.",
                    "category": "Web Development",
                    "topic": "React Internals & Fiber",
                    "expected_focus": ["Interruptible rendering work units", "Urgent vs non-urgent transitions", "Suspense streaming boundaries"],
                },
                {
                    "question": "How would you architect a Micro-Frontend system using Webpack Module Federation with independent CI/CD deployments?",
                    "category": "System Design",
                    "topic": "Micro-Frontends Architecture",
                    "expected_focus": ["Host vs remote containers", "Shared vendor singletons (React instance)", "Cross-app routing and error boundaries"],
                },
                {
                    "question": "Compare Server-Side Rendering (SSR), Static Site Generation (SSG), Incremental Static Regeneration (ISR), and Client-Side Hydration.",
                    "category": "System Design",
                    "topic": "Modern Rendering Strategies",
                    "expected_focus": ["Hydration mismatch debugging", "Edge rendering and streaming SSR", "Build time vs freshness tradeoffs"],
                },
                {
                    "question": "How do you build a completely accessible (WCAG 2.1 AA) design system with custom interactive comboboxes, dialogs, and keyboard navigation?",
                    "category": "Web Development",
                    "topic": "Accessibility & Design Systems",
                    "expected_focus": ["WAI-ARIA roles & aria-expanded/aria-activedescendant", "Focus trapping and restoration", "Screen reader announcements (aria-live)"],
                },
                {
                    "question": "How do you optimize browser rendering pipelines (Recalculate Style, Layout, Paint, Composite) to achieve a smooth 60fps animation?",
                    "category": "Technical",
                    "topic": "Browser Graphics & Compositing",
                    "expected_focus": ["transform and opacity triggering GPU compositing", "Avoiding layout thrashing and reflows", "will-change usage caveats"],
                },
            ],
        },
    },
    "Backend Developer": {
        "Technical": {
            "Beginner": [
                {
                    "question": "Explain the difference between synchronous and asynchronous I/O in backend servers, and why it matters for scaling.",
                    "category": "Technical",
                    "topic": "Server Concurrency",
                    "expected_focus": ["Thread-per-request limitations", "Non-blocking event-driven loop", "Handling high concurrent connections"],
                },
                {
                    "question": "Explain how relational database primary keys, foreign keys, and unique constraints preserve relational integrity.",
                    "category": "Database",
                    "topic": "Relational Data Modeling",
                    "expected_focus": ["Entity identity", "Referential integrity and cascade rules", "Preventing duplicate records"],
                },
                {
                    "question": "What is the difference between authentication and authorization in backend security, and what protocols implement each?",
                    "category": "Technical",
                    "topic": "Auth & Access Control",
                    "expected_focus": ["Identity verification vs permissions", "Role-Based Access Control (RBAC)", "JWT and session tokens"],
                },
                {
                    "question": "Explain the anatomy of an HTTP request and response, including status code ranges (2xx, 3xx, 4xx, 5xx).",
                    "category": "Technical",
                    "topic": "HTTP Protocol",
                    "expected_focus": ["Headers, body, status codes", "Client error (401/403/404) vs server error (500/502/504)", "Content-Type negotiation"],
                },
                {
                    "question": "What is an ORM (Object-Relational Mapper), and what are the pros and cons of using one compared to raw SQL queries?",
                    "category": "Database",
                    "topic": "Database Abstractions",
                    "expected_focus": ["Developer velocity and type safety", "The N+1 query problem", "Complex query performance limitations"],
                },
            ],
            "Intermediate": [
                {
                    "question": "How does database indexing (B-Tree vs Hash index) optimize query execution, and when can indexes hurt performance?",
                    "category": "Database",
                    "topic": "Indexing & Query Optimization",
                    "expected_focus": ["Index lookup vs full table scan", "Write amplification on INSERT/UPDATE", "Composite index column order"],
                },
                {
                    "question": "How do you implement caching strategies (Cache-Aside, Write-Through, Write-Back) using Redis to reduce database strain?",
                    "category": "System Design",
                    "topic": "Distributed Caching",
                    "expected_focus": ["Cache-Aside pattern implementation", "Cache invalidation strategies", "Thundering herd / cache stampede protection"],
                },
                {
                    "question": "Explain database transaction isolation levels (Read Uncommitted, Read Committed, Repeatable Read, Serializable) and concurrency anomalies.",
                    "category": "Database",
                    "topic": "ACID & Transactions",
                    "expected_focus": ["Dirty reads, non-repeatable reads, phantom reads", "Multi-Version Concurrency Control (MVCC)", "Pessimistic vs Optimistic locking"],
                },
                {
                    "question": "How do you build a resilient rate-limiter for backend APIs to prevent abuse while allowing burst traffic?",
                    "category": "System Design",
                    "topic": "API Rate Limiting",
                    "expected_focus": ["Token Bucket vs Sliding Window Log algorithms", "Redis atomic operations (INCR/EXPIRE)", "429 Too Many Requests response headers"],
                },
                {
                    "question": "What strategies do you use for centralized logging, structured error tracing, and distributed request correlation in microservices?",
                    "category": "Problem Solving",
                    "topic": "Observability & Tracing",
                    "expected_focus": ["Correlation ID / Trace ID propagation", "JSON structured logs", "OpenTelemetry / APM standards"],
                },
            ],
            "Advanced": [
                {
                    "question": "How do you design a high-throughput event ingestion pipeline processing 100,000 events/second with Kafka and distributed consumers?",
                    "category": "System Design",
                    "topic": "Event Streaming & Scale",
                    "expected_focus": ["Partitioning keys and consumer rebalancing", "Backpressure handling", "At-least-once vs exactly-once delivery guarantees"],
                },
                {
                    "question": "How would you architect a distributed transaction across multiple microservices without using a blocking two-phase commit?",
                    "category": "System Design",
                    "topic": "Saga Pattern & Distributed Transactions",
                    "expected_focus": ["Choreography vs Orchestration Sagas", "Compensating transactions for rollback", "Eventual consistency reconciliation"],
                },
                {
                    "question": "Deep dive into database connection pooling: how do you tune pool size, thread saturation, and handle connection exhaustion?",
                    "category": "Database",
                    "topic": "Connection Management",
                    "expected_focus": ["HikariCP / PgBouncer sizing formulas", "CPU core vs disk spindle balance", "Connection timeout and health checks"],
                },
                {
                    "question": "How do you design a database sharding architecture for a multi-tenant platform with petabyte-scale data growth?",
                    "category": "System Design",
                    "topic": "Database Sharding",
                    "expected_focus": ["Shard key selection criteria", "Consistent hashing and shard rebalancing", "Cross-shard join and aggregation avoidance"],
                },
                {
                    "question": "Explain how gRPC and Protocol Buffers compare to REST/JSON in terms of network serialization efficiency, HTTP/2 streaming, and typed contracts.",
                    "category": "Technical",
                    "topic": "RPC Protocols & Networking",
                    "expected_focus": ["Binary serialization vs textual JSON", "Multiplexing and bidirectional streaming", "Backward compatibility with field tags"],
                },
            ],
        },
    },
    "Full Stack Developer": {
        "Technical": {
            "Beginner": [
                {
                    "question": "Explain the end-to-end lifecycle of a web request from the moment a user clicks a button to the database query response.",
                    "category": "Web Development",
                    "topic": "Web Architecture",
                    "expected_focus": ["Client event handler", "HTTP request and CORS checks", "Server routing, middleware, database query, and UI render"],
                },
                {
                    "question": "What is the difference between state and props in React, and how does data flow down to child components?",
                    "category": "Web Development",
                    "topic": "React Fundamentals",
                    "expected_focus": ["Unidirectional data flow", "State mutability vs prop immutability", "Lifting state up to common ancestors"],
                },
                {
                    "question": "What is the difference between SQL and NoSQL databases, and what criteria guide your selection for a new project?",
                    "category": "Database",
                    "topic": "Database Selection",
                    "expected_focus": ["Structured schema vs flexible document model", "ACID guarantees vs horizontal scaling ease", "Complex joins vs high-velocity writes"],
                },
                {
                    "question": "Explain how RESTful conventions determine HTTP verbs (GET, POST, PUT, DELETE) and status codes.",
                    "category": "Technical",
                    "topic": "REST APIs",
                    "expected_focus": ["Idempotence of PUT/DELETE vs non-idempotent POST", "Resource URIs without verbs in path", "200, 201, 400, 401, 404 meaning"],
                },
                {
                    "question": "How do cookies, localStorage, and sessionStorage differ in terms of lifespan, capacity, and security vulnerabilities?",
                    "category": "Web Development",
                    "topic": "Client Storage Security",
                    "expected_focus": ["Storage limits (5MB vs 4KB)", "HttpOnly flag preventing XSS token theft", "Session lifetime scope"],
                },
            ],
            "Intermediate": [
                {
                    "question": "How do you implement secure JWT-based authentication in a full stack app, preventing XSS and CSRF token theft?",
                    "category": "Technical",
                    "topic": "Web Security",
                    "expected_focus": ["HttpOnly SameSite cookies vs LocalStorage", "Short-lived access tokens with refresh token rotation", "CSRF protection tokens"],
                },
                {
                    "question": "Explain React's reconciliation diffing algorithm and why using array indices as element keys causes subtle bugs.",
                    "category": "Web Development",
                    "topic": "React Internals",
                    "expected_focus": ["O(n) heuristic diffing algorithm", "Key identity for DOM node reuse", "Component state mixing on item deletion"],
                },
                {
                    "question": "How would you design a database indexing and compound index strategy for high-frequency queries in PostgreSQL or MongoDB?",
                    "category": "Database",
                    "topic": "Query Optimization",
                    "expected_focus": ["B-tree indexes", "Compound indexes and field order (Equality, Sort, Range)", "EXPLAIN ANALYZE execution plans"],
                },
                {
                    "question": "What strategies do you use for unified error handling across both backend APIs and React frontend error boundaries?",
                    "category": "Problem Solving",
                    "topic": "Full-Stack Error Architecture",
                    "expected_focus": ["Standard error payload formats", "React ErrorBoundary fallbacks", "Toast notifications and user-friendly alerts"],
                },
                {
                    "question": "How does containerization with Docker improve full-stack development, and how do you structure multi-stage builds for production?",
                    "category": "Technical",
                    "topic": "DevOps & Containers",
                    "expected_focus": ["Environment parity", "Multi-stage build separation (build vs runtime)", "Minimizing image size and security attack surface"],
                },
            ],
            "Advanced": [
                {
                    "question": "How would you architect a real-time collaborative application using WebSockets, Redis pub/sub, and optimistic client updates?",
                    "category": "System Design",
                    "topic": "Real-time Collaboration",
                    "expected_focus": ["Scaling WebSocket connections behind load balancers", "Conflict resolution (CRDTs or Operational Transformation)", "Heartbeats and graceful reconnection"],
                },
                {
                    "question": "Compare Server-Side Rendering (SSR), Static Site Generation (SSG), and Client-Side Rendering (CSR) with regards to Core Web Vitals.",
                    "category": "Web Development",
                    "topic": "Rendering Strategies",
                    "expected_focus": ["FCP, LCP, CLS trade-offs", "Hydration overhead and Server Components", "Edge caching and streaming HTML"],
                },
                {
                    "question": "How do you handle database migration, zero-downtime deployments, and schema backwards compatibility in a continuous deployment pipeline?",
                    "category": "System Design",
                    "topic": "Deployment Architecture",
                    "expected_focus": ["Blue/green and canary deployments", "Expand and contract schema migration pattern", "Feature flags for safe rollouts"],
                },
                {
                    "question": "Explain micro-frontend architectures: how do module federation and isolated sub-apps solve scaling problems for large teams?",
                    "category": "System Design",
                    "topic": "Frontend Architecture",
                    "expected_focus": ["Shared runtime dependencies", "Independent deployment cadences", "Routing and state containment"],
                },
                {
                    "question": "How would you design rate-limiting, DDoS mitigation, and distributed caching for an API gateway serving 50k requests/sec?",
                    "category": "System Design",
                    "topic": "API Gateway & Scale",
                    "expected_focus": ["Token bucket / Leaky bucket algorithms", "Redis cluster caching", "Cache-Control headers & CDN edge distribution"],
                },
            ],
        },
    },
    "Python Developer": {
        "Technical": {
            "Beginner": [
                {
                    "question": "Explain the difference between mutable and immutable data types in Python with practical examples.",
                    "category": "Technical",
                    "topic": "Python Fundamentals",
                    "expected_focus": ["Lists/dicts vs tuples/strings", "Memory address/id() behavior", "In-place modifications vs new object allocation"],
                },
                {
                    "question": "How do list comprehensions work in Python, and when should you prefer them over traditional for loops?",
                    "category": "Coding",
                    "topic": "Python Idioms",
                    "expected_focus": ["Syntactic readability", "C-level bytecode execution speed", "Avoiding overly complex nested expressions"],
                },
                {
                    "question": "What is the difference between shallow copy and deep copy in Python's copy module?",
                    "category": "Programming",
                    "topic": "Object References",
                    "expected_focus": ["copy.copy vs copy.deepcopy", "Nested mutable objects", "Compound object references"],
                },
                {
                    "question": "Explain how Python handles exception handling with try, except, else, and finally blocks.",
                    "category": "Technical",
                    "topic": "Error Handling",
                    "expected_focus": ["Catching specific exceptions", "When the else block runs", "Guaranteed cleanup in finally"],
                },
                {
                    "question": "What are *args and **kwargs in Python functions, and how are they commonly used in wrapper functions?",
                    "category": "Programming",
                    "topic": "Function Signatures",
                    "expected_focus": ["Variable positional arguments", "Keyword argument unpacking", "Writing generic function decorators"],
                },
            ],
            "Intermediate": [
                {
                    "question": "Explain the Python Global Interpreter Lock (GIL) and how it affects multithreaded CPU-bound versus I/O-bound tasks.",
                    "category": "Technical",
                    "topic": "Concurrency & Internals",
                    "expected_focus": ["Thread safety in CPython memory management", "Multiprocessing for CPU-bound tasks", "AsyncIO / threading for I/O-bound tasks"],
                },
                {
                    "question": "How do Python decorators work under the hood, and how would you implement a decorator that takes custom arguments?",
                    "category": "Programming",
                    "topic": "Metaprogramming & Decorators",
                    "expected_focus": ["First-class functions and closures", "functools.wraps preserving metadata", "Three-level nested functions for arguments"],
                },
                {
                    "question": "What are Python generators and the 'yield' statement, and what memory advantages do they offer over full lists?",
                    "category": "Technical",
                    "topic": "Generators & Iterators",
                    "expected_focus": ["Lazy evaluation stream processing", "Iterator protocol (__iter__ and __next__)", "Constant O(1) memory usage"],
                },
                {
                    "question": "How does context management (__enter__ and __exit__) work with Python's 'with' statement?",
                    "category": "Technical",
                    "topic": "Context Managers",
                    "expected_focus": ["Deterministic resource cleanup (file handles, sockets)", "contextlib.contextmanager generator syntax", "Exception suppression logic"],
                },
                {
                    "question": "Compare dependency injection and ORM patterns in modern Python frameworks like FastAPI and Django.",
                    "category": "System Design",
                    "topic": "Framework Architecture",
                    "expected_focus": ["FastAPI Depends() dependency injection", "SQLAlchemy 2.0 vs Django ORM", "Unit testing with mocked dependencies"],
                },
            ],
            "Advanced": [
                {
                    "question": "How does Python's cyclic garbage collector detect and collect circular reference memory leaks?",
                    "category": "Technical",
                    "topic": "Memory Management & GC",
                    "expected_focus": ["Reference counting as primary mechanism", "Generational GC (Gen 0, Gen 1, Gen 2)", "gc module heuristics and weak references"],
                },
                {
                    "question": "Explain metaclasses in Python. How do type.__new__ and type.__init__ work during dynamic class creation?",
                    "category": "Programming",
                    "topic": "Metaclasses & Class Construction",
                    "expected_focus": ["type as the metaclass of classes", "__prepare__ dict creation", "Class registry, ORM schema definition, and validation"],
                },
                {
                    "question": "Deep dive into AsyncIO event loops: how does uvloop optimize task execution compared to the default asyncio loop?",
                    "category": "System Design",
                    "topic": "Async Architecture",
                    "expected_focus": ["libuv C-library integration", "Coroutines vs Tasks vs Futures", "Preventing blocking synchronous calls in async code"],
                },
                {
                    "question": "How would you design a distributed worker architecture in Python that processes millions of tasks with at-least-once delivery?",
                    "category": "System Design",
                    "topic": "Distributed Systems",
                    "expected_focus": ["Celery / Redis / RabbitMQ broker", "Idempotency keys and atomic state updates", "Dead letter queues, visibility timeouts, and worker prefetch"],
                },
                {
                    "question": "How does CPython bytecode execution and the eval loop function, and how does Python 3.12+ specialize bytecode with Tier 2 JIT optimizations?",
                    "category": "Technical",
                    "topic": "Compiler & Bytecode",
                    "expected_focus": ["dis module bytecode inspection", "Adaptive specializing interpreter (PEP 659)", "Opcode inline caching and type specialization"],
                },
            ],
        },
    },
    "Java Developer": {
        "Technical": {
            "Beginner": [
                {
                    "question": "Explain the difference between JDK, JRE, and JVM in the Java ecosystem.",
                    "category": "Technical",
                    "topic": "Java Architecture",
                    "expected_focus": ["Java Development Kit components", "Java Runtime Environment", "Java Virtual Machine bytecode execution and platform independence"],
                },
                {
                    "question": "What is the difference between '==' and '.equals()' in Java, and why must you override hashCode() when overriding equals()?",
                    "category": "Programming",
                    "topic": "Java Fundamentals",
                    "expected_focus": ["Reference identity vs object value equality", "Hash-based collections contract (HashMap / HashSet)", "Bucket indexing consistency"],
                },
                {
                    "question": "Explain the difference between Abstract Classes and Interfaces in Java 8+.",
                    "category": "Programming",
                    "topic": "OOP in Java",
                    "expected_focus": ["Single class inheritance vs multiple interface implementation", "Default and static methods in interfaces", "State and constructor capabilities"],
                },
                {
                    "question": "What is the difference between checked and unchecked exceptions in Java?",
                    "category": "Technical",
                    "topic": "Exception Handling",
                    "expected_focus": ["Compile-time checking (Exception) vs RuntimeException", "When to recover vs when to fail fast", "try-with-resources statement"],
                },
                {
                    "question": "Explain how the Java Collections Framework organizes List, Set, and Map interfaces.",
                    "category": "Coding",
                    "topic": "Collections Framework",
                    "expected_focus": ["ArrayList vs LinkedList", "HashSet vs TreeSet ordering", "HashMap key-value mapping"],
                },
            ],
            "Intermediate": [
                {
                    "question": "Explain the JVM Memory Model: Heap (Young Gen / Old Gen), Metaspace, and Stack memory.",
                    "category": "Technical",
                    "topic": "JVM Internals",
                    "expected_focus": ["Stack memory per thread vs shared Heap", "Young Gen (Eden, S0, S1) minor GC vs Old Gen major GC", "OutOfMemoryError vs StackOverflowError"],
                },
                {
                    "question": "How does Spring Boot implement Inversion of Control (IoC) and Dependency Injection (DI) with annotations like @Component, @Service, and @Autowired?",
                    "category": "Programming",
                    "topic": "Spring Framework",
                    "expected_focus": ["Spring ApplicationContext lifecycle", "Constructor injection vs Field injection", "Bean scopes (Singleton, Prototype)"],
                },
                {
                    "question": "Explain Java Concurrency: synchronized blocks, volatile keyword, and Atomic variables (AtomicInteger).",
                    "category": "Technical",
                    "topic": "Multithreading",
                    "expected_focus": ["Mutual exclusion locks", "Visibility guarantees and cache coherence with volatile", "Compare-And-Swap (CAS) non-blocking operations"],
                },
                {
                    "question": "How do Java 8+ Streams and lambda expressions work, and what is the difference between intermediate and terminal operations?",
                    "category": "Coding",
                    "topic": "Java Streams",
                    "expected_focus": ["Lazy evaluation pipeline", "map/filter intermediate vs collect/reduce terminal", "Parallel streams overhead cautions"],
                },
                {
                    "question": "How does Hibernate / JPA manage Entity lifecycles (Transient, Persistent, Detached, Removed) and solve the N+1 select problem?",
                    "category": "Database",
                    "topic": "JPA & Hibernate",
                    "expected_focus": ["EntityManager persistence context", "JOIN FETCH queries and EntityGraphs", "First-level vs second-level cache"],
                },
            ],
            "Advanced": [
                {
                    "question": "Compare modern JVM Garbage Collectors: G1GC, ZGC, and Shenandoah. How do concurrent GC algorithms achieve low latency (<1ms pause)?",
                    "category": "Technical",
                    "topic": "GC Tuning & Internals",
                    "expected_focus": ["Stop-the-world pauses vs concurrent marking", "Colored pointers and load barriers in ZGC", "Region-based memory management"],
                },
                {
                    "question": "Explain Project Loom and Java Virtual Threads: how do continuation-based lightweight threads scale high-throughput I/O servers?",
                    "category": "Technical",
                    "topic": "Virtual Threads (Java 21)",
                    "expected_focus": ["Platform OS threads vs user-space Virtual Threads", "Carrier thread mounting/unmounting", "Pinning caveats with synchronized blocks"],
                },
                {
                    "question": "How do you design a high-throughput reactive microservice using Spring WebFlux, Project Reactor, and non-blocking database drivers (R2DBC)?",
                    "category": "System Design",
                    "topic": "Reactive Architecture",
                    "expected_focus": ["Reactive Streams specification (Publisher, Subscriber, Subscription)", "Backpressure management", "EventLoop scheduling without thread starvation"],
                },
                {
                    "question": "Deep dive into ConcurrentHashMap in Java 8+: how does it eliminate table-wide locks using CAS and synchronized bucket nodes?",
                    "category": "Coding",
                    "topic": "Concurrent Data Structures",
                    "expected_focus": ["Bucket-level synchronization", "Tree bins (Red-Black tree conversion at threshold 8)", "Lock-free reads"],
                },
                {
                    "question": "How does the JVM Just-In-Time (JIT) compiler (C1, C2/Graal) perform optimizations like Method Inlining, Escape Analysis, and Loop Unrolling?",
                    "category": "Technical",
                    "topic": "JIT Compilation",
                    "expected_focus": ["Tiered compilation thresholds", "Stack allocation via Escape Analysis", "Deoptimization and on-stack replacement (OSR)"],
                },
            ],
        },
    },
    "Data Analyst": {
        "Technical": {
            "Beginner": [
                {
                    "question": "Explain the difference between INNER JOIN, LEFT JOIN, RIGHT JOIN, and FULL OUTER JOIN in SQL with examples.",
                    "category": "Database",
                    "topic": "SQL Joins",
                    "expected_focus": ["Matching rows across tables", "Preserving unmatched rows from left/right", "Handling NULL values resulting from joins"],
                },
                {
                    "question": "What is the difference between WHERE and HAVING clauses in SQL aggregations?",
                    "category": "Database",
                    "topic": "SQL Filtering & Aggregations",
                    "expected_focus": ["Row-level filtering before GROUP BY (WHERE)", "Aggregate condition filtering after GROUP BY (HAVING)", "Query execution order"],
                },
                {
                    "question": "In Excel or Google Sheets, how do VLOOKUP, INDEX/MATCH, and XLOOKUP differ in flexibility and performance?",
                    "category": "Problem Solving",
                    "topic": "Spreadsheet Modeling",
                    "expected_focus": ["Left-lookup limitations of VLOOKUP", "Dynamic column referencing in INDEX/MATCH", "Exact match and return array in XLOOKUP"],
                },
                {
                    "question": "What is the difference between Mean, Median, and Mode, and when is the Median preferred for reporting?",
                    "category": "Technical",
                    "topic": "Descriptive Statistics",
                    "expected_focus": ["Central tendency measures", "Sensitivity of Mean to extreme outliers / skewed distributions", "Income or real-estate examples"],
                },
                {
                    "question": "How do you detect and clean missing or duplicated records in a raw dataset using Python (Pandas) or SQL?",
                    "category": "Coding",
                    "topic": "Data Cleaning",
                    "expected_focus": ["dropna() vs fillna() with mean/median", "drop_duplicates()", "Imputation risks and bias"],
                },
            ],
            "Intermediate": [
                {
                    "question": "Explain SQL Window Functions: ROW_NUMBER(), RANK(), DENSE_RANK(), and LEAD()/LAG() with use cases.",
                    "category": "Database",
                    "topic": "Advanced SQL",
                    "expected_focus": ["PARTITION BY and ORDER BY clauses", "Handling ties with RANK vs DENSE_RANK", "Time-series difference calculation with LAG"],
                },
                {
                    "question": "How do you design an A/B test: what steps ensure statistical significance, adequate sample size, and p-value validation?",
                    "category": "Technical",
                    "topic": "A/B Testing & Hypothesis Testing",
                    "expected_focus": ["Null vs Alternative hypothesis", "Type I (alpha) and Type II (beta) errors", "Statistical power and minimum detectable effect (MDE)"],
                },
                {
                    "question": "What are primary chart selection principles for dashboards: when should you use a Bar chart, Line chart, Scatter plot, or Heatmap?",
                    "category": "Problem Solving",
                    "topic": "Data Visualization & Storytelling",
                    "expected_focus": ["Categorical comparison vs temporal trend vs correlation", "Avoiding pie chart clutter", "Effective color hierarchy and cognitive load"],
                },
                {
                    "question": "Explain Star Schema vs Snowflake Schema in dimensional data modeling for analytics data warehouses.",
                    "category": "Database",
                    "topic": "Data Warehousing",
                    "expected_focus": ["Fact tables and Dimension tables", "Denormalized dimensions in Star Schema for fast joins", "Normalized hierarchies in Snowflake Schema"],
                },
                {
                    "question": "How do you build a customer cohort analysis or retention curve in SQL or Python to analyze churn rates over time?",
                    "category": "Problem Solving",
                    "topic": "Cohort & Retention Analysis",
                    "expected_focus": ["Cohort definition by signup month", "Monthly active retention percentage matrix", "Identifying product retention plateaus"],
                },
            ],
            "Advanced": [
                {
                    "question": "How do you detect and mitigate Simpson's Paradox or confounding variables in observational business datasets?",
                    "category": "Technical",
                    "topic": "Statistical Fallacies & Causal Inference",
                    "expected_focus": ["Subgroup trend reversal in aggregated data", "Stratification and multivariate regression controls", "Real business case example"],
                },
                {
                    "question": "How do you optimize slow analytical queries on petabyte-scale cloud data warehouses (e.g. BigQuery, Snowflake, Redshift)?",
                    "category": "Database",
                    "topic": "Data Warehouse Optimization",
                    "expected_focus": ["Partitioning and clustering strategies", "Avoiding SELECT * to reduce bytes scanned", "Materialized views and query pruning"],
                },
                {
                    "question": "Explain how you construct an Automated Anomaly Detection framework for daily business KPIs (e.g. Sudden Drop in Conversion Rate).",
                    "category": "Problem Solving",
                    "topic": "Metric Monitoring & Anomaly Detection",
                    "expected_focus": ["Z-score / IQR outlier boundaries", "Accounting for seasonality and day-of-week effects", "Alert fatigue prevention and root cause triage"],
                },
                {
                    "question": "Compare Customer Lifetime Value (LTV) modeling methods: historical cohort average vs predictive probabilistic models (BG/NBD).",
                    "category": "Technical",
                    "topic": "Predictive Customer Analytics",
                    "expected_focus": ["Recency, Frequency, Monetary (RFM) segmentation", "Expected future transaction modeling", "Guiding customer acquisition cost (CAC) ceilings"],
                },
                {
                    "question": "How do you establish Data Governance, metric consistency, and a Single Source of Truth across multiple self-service BI tools?",
                    "category": "System Design",
                    "topic": "Data Governance & Semantic Layers",
                    "expected_focus": ["Semantic layer definitions (dbt metrics / Looker LookML)", "Data lineage and automated quality tests", "Documentation and data dictionary ownership"],
                },
            ],
        },
    },
    "AI/ML Engineer": {
        "Technical": {
            "Beginner": [
                {
                    "question": "Explain the difference between Supervised Learning, Unsupervised Learning, and Reinforcement Learning with practical examples.",
                    "category": "Technical",
                    "topic": "Machine Learning Fundamentals",
                    "expected_focus": ["Labeled data for classification/regression", "Clustering and dimensionality reduction on unlabeled data", "Agent, environment, policy, and reward loop"],
                },
                {
                    "question": "What is the Bias-Variance Tradeoff, and how do underfitting and overfitting manifest during model training and evaluation?",
                    "category": "Technical",
                    "topic": "Model Generalization",
                    "expected_focus": ["High bias causing underfitting", "High variance causing overfitting on training data", "Train vs validation loss curve behavior"],
                },
                {
                    "question": "Explain Gradient Descent and describe how the Learning Rate parameter influences model convergence.",
                    "category": "Coding",
                    "topic": "Optimization Algorithms",
                    "expected_focus": ["Loss surface gradients", "Divergence with too high learning rate vs slow convergence with too low", "Stochastic vs Batch Gradient Descent"],
                },
                {
                    "question": "What is the difference between Precision, Recall, F1-Score, and Accuracy, and why is Accuracy misleading for imbalanced datasets?",
                    "category": "Technical",
                    "topic": "Model Evaluation Metrics",
                    "expected_focus": ["Confusion matrix (TP, FP, TN, FN)", "False positive vs false negative penalties", "F1 as harmonic mean for rare event detection"],
                },
                {
                    "question": "Explain common regularization techniques (L1 Lasso, L2 Ridge, and Dropout in neural networks) that prevent overfitting.",
                    "category": "Technical",
                    "topic": "Regularization Techniques",
                    "expected_focus": ["L1 sparsity feature selection", "L2 weight penalty shrink", "Dropout randomly disabling neurons during forward pass"],
                },
            ],
            "Intermediate": [
                {
                    "question": "Explain the Transformer architecture: what is the role of Self-Attention, Multi-Head Attention, and Positional Encodings?",
                    "category": "Technical",
                    "topic": "Transformer Architecture",
                    "expected_focus": ["Query, Key, Value dot-product attention formula", "Multi-head attention capturing distinct contextual subspace representations", "Injecting sequence order into permutation-invariant attention"],
                },
                {
                    "question": "Compare fine-tuning strategies for Large Language Models: Full Fine-Tuning vs Parameter-Efficient Fine-Tuning (LoRA / QLoRA).",
                    "category": "Technical",
                    "topic": "LLM Fine-Tuning & PEFT",
                    "expected_focus": ["Computational cost and catastrophic forgetting", "Low-Rank Adaptation matrix decomposition (W = W0 + B*A)", "4-bit quantization in QLoRA saving GPU VRAM"],
                },
                {
                    "question": "How does Retrieval-Augmented Generation (RAG) work: describe the chunking, embedding, vector search, and reranking pipeline.",
                    "category": "System Design",
                    "topic": "RAG Systems",
                    "expected_focus": ["Text chunking strategies with overlap", "Dense vector embeddings and Approximate Nearest Neighbor (HNSW) search", "Cross-encoder reranking and prompt grounding"],
                },
                {
                    "question": "What strategies mitigate Hallucinations in production LLM applications?",
                    "category": "Problem Solving",
                    "topic": "LLM Reliability & Safety",
                    "expected_focus": ["Strict system prompt guardrails and output schema enforcement", "RAG citation verification", "Temperature reduction and self-consistency checking"],
                },
                {
                    "question": "How do you detect Data Drift and Concept Drift in a production ML deployment, and when do you trigger automated retraining?",
                    "category": "Problem Solving",
                    "topic": "MLOps & Monitoring",
                    "expected_focus": ["Feature distribution shift (KS-test / PSI metric)", "Input-to-label relationship changes (Concept Drift)", "Automated canary evaluation and rollback"],
                },
            ],
            "Advanced": [
                {
                    "question": "How would you architect a low-latency, high-throughput LLM serving infrastructure using vLLM, PagedAttention, and Tensor Parallelism?",
                    "category": "System Design",
                    "topic": "Inference Optimization & Serving",
                    "expected_focus": ["PagedAttention eliminating KV-cache memory fragmentation", "Continuous batching", "Multi-GPU Tensor Parallelism across NVLink"],
                },
                {
                    "question": "Deep dive into Reinforcement Learning from Human Feedback (RLHF) vs Direct Preference Optimization (DPO) for aligning LLMs.",
                    "category": "Technical",
                    "topic": "LLM Alignment",
                    "expected_focus": ["Reward model training on human preference pairs", "PPO policy optimization with KL-divergence penalty", "DPO closed-form optimization bypassing separate reward models"],
                },
                {
                    "question": "How do you scale distributed deep learning training across hundreds of GPUs using DeepSpeed ZeRO (Stages 1, 2, 3) and FSDP?",
                    "category": "System Design",
                    "topic": "Distributed Training",
                    "expected_focus": ["Optimizer state partitioning (ZeRO-1)", "Gradient partitioning (ZeRO-2)", "Parameter sharding and all-gather communication (ZeRO-3/FSDP)"],
                },
                {
                    "question": "Explain the mechanics of Quantization (PTQ vs QAT, INT8, FP4, AWQ) and its impact on perplexity versus memory bandwidth.",
                    "category": "Technical",
                    "topic": "Model Quantization & Pruning",
                    "expected_focus": ["Post-Training Quantization vs Quantization-Aware Training", "Activation outliers preservation in AWQ/SmoothQuant", "Memory bandwidth vs compute bound regime in autoregressive generation"],
                },
                {
                    "question": "How do you design a real-time multimodal model pipeline that processes continuous audio and video streams with sub-500ms time-to-first-token?",
                    "category": "System Design",
                    "topic": "Multimodal Systems Architecture",
                    "expected_focus": ["Streaming tokenization (chunked audio encoders)", "Vision cross-attention injection", "Speculative decoding and edge caching"],
                },
            ],
        },
    },
}

# ==============================================================================
# Comprehensive HR & Behavioral Question Bank Across Difficulty Levels
# ==============================================================================
HR_QUESTIONS_DB: Dict[str, List[Dict[str, Any]]] = {
    "Beginner": [
        {
            "question": "Tell me about yourself, your background, and what inspired you to pursue a career in this field.",
            "category": "HR",
            "topic": "Professional Introduction",
            "expected_focus": ["Concise career journey", "Key technical passions", "Alignment with company culture"],
        },
        {
            "question": "What do you consider your greatest technical strength, and what is one skill area you are actively working to improve?",
            "category": "HR",
            "topic": "Self-Awareness & Growth",
            "expected_focus": ["Concrete strength with evidence", "Honest area for development", "Proactive steps taken to improve"],
        },
        {
            "question": "Describe a project you worked on where you collaborated with others. How did you coordinate and divide responsibilities?",
            "category": "Behavioral",
            "topic": "Teamwork & Collaboration",
            "expected_focus": ["Clear role distribution", "Communication cadence", "Delivering joint outcomes"],
        },
        {
            "question": "Where do you see yourself professionally in two to three years, and how does this role fit into those aspirations?",
            "category": "HR",
            "topic": "Career Goals",
            "expected_focus": ["Ambition and commitment", "Desire for technical depth", "Value delivery to team"],
        },
        {
            "question": "Tell me about a time when you were stuck on a difficult bug or challenge. How did you approach troubleshooting it?",
            "category": "Situational",
            "topic": "Problem Solving Under Pressure",
            "expected_focus": ["Systematic debugging approach", "Knowing when to seek help", "Key lesson learned"],
        },
        {
            "question": "How do you stay updated with rapid advancements and emerging technologies in software engineering?",
            "category": "HR",
            "topic": "Continuous Learning",
            "expected_focus": ["Tech blogs and documentation", "Side projects and experimentation", "Open source exploration"],
        },
        {
            "question": "Describe a time when you received constructive criticism on your code or work. How did you react?",
            "category": "Behavioral",
            "topic": "Receptiveness to Feedback",
            "expected_focus": ["Non-defensive attitude", "Implementing suggestions", "Improving subsequent work"],
        },
        {
            "question": "How do you prioritize your tasks when you have multiple assignments or deadlines competing for your time?",
            "category": "Situational",
            "topic": "Time Management",
            "expected_focus": ["Eisenhower matrix / urgency vs importance", "Transparent communication with leads", "Focusing on MVP delivery"],
        },
    ],
    "Intermediate": [
        {
            "question": "Describe a situation where you had a strong technical disagreement with a colleague or lead. How did you handle the debate and reach a resolution?",
            "category": "Behavioral",
            "topic": "Conflict Resolution",
            "expected_focus": ["Respectful debate centered on data", "Weighing architectural tradeoffs", "Committing fully to the final team decision"],
        },
        {
            "question": "Tell me about a time when requirements shifted dramatically midway through a sprint. How did you pivot and maintain delivery velocity?",
            "category": "Situational",
            "topic": "Adaptability & Agility",
            "expected_focus": ["Scope renegotiation with product managers", "Pragmatic code refactoring", "Keeping stakeholders informed"],
        },
        {
            "question": "How do you cultivate an empathetic and constructive code review culture within an engineering squad?",
            "category": "Behavioral",
            "topic": "Code Review & Team Standards",
            "expected_focus": ["Critiquing code rather than the author", "Explaining the 'why' behind feedback", "Balancing perfectionism with shipping velocity"],
        },
        {
            "question": "Describe a project where you took the initiative to refactor an inefficient system or automate a repetitive manual workflow without being assigned to do so.",
            "category": "Behavioral",
            "topic": "Ownership & Initiative",
            "expected_focus": ["Recognizing operational bottlenecks", "Building a business case or quick POC", "Measurable time or cost savings"],
        },
        {
            "question": "Can you share an experience where a production deployment or project release failed? How did you respond during the incident and what preventative measures did you institute?",
            "category": "Behavioral",
            "topic": "Failure Analysis & Resilience",
            "expected_focus": ["Calm incident management", "Blameless post-mortem analysis", "Adding monitoring alarms or automated tests"],
        },
        {
            "question": "Describe a scenario where you had to onboard or mentor a newer engineer. How did you accelerate their time-to-productivity?",
            "category": "HR",
            "topic": "Mentorship & Knowledge Sharing",
            "expected_focus": ["Pair programming and clear documentation", "Creating psychological safety for questions", "Empowering independent problem-solving"],
        },
        {
            "question": "How do you handle a situation where a stakeholder demands an unrealistic delivery deadline?",
            "category": "Situational",
            "topic": "Stakeholder Management",
            "expected_focus": ["Transparent timeline estimation", "Proposing phased delivery (P0/P1 scope)", "Protecting code quality and avoiding burnout"],
        },
    ],
    "Advanced": [
        {
            "question": "Describe a major architectural migration you led that required buy-in from multiple engineering teams with competing priorities.",
            "category": "HR",
            "topic": "Technical Leadership & Influence",
            "expected_focus": ["Architecture Decision Records (ADRs)", "Aligning disparate stakeholders", "Incremental phased rollout minimizing disruptions"],
        },
        {
            "question": "How do you balance paying down technical debt against urgent commercial feature demands when negotiating roadmaps with executives?",
            "category": "Situational",
            "topic": "Strategic Prioritization",
            "expected_focus": ["Quantifying business cost of latency/outages", "Negotiating dedicated tech-debt allocation (e.g. 20%)", "Pragmatic business-first compromise"],
        },
        {
            "question": "Tell me about a high-stakes technical decision you had to make under extreme ambiguity and incomplete data. What was your framework?",
            "category": "Behavioral",
            "topic": "Decision-Making Under Ambiguity",
            "expected_focus": ["Assessing one-way vs two-way doors", "Rapid proof-of-concept validation", "Risk mitigation and contingency planning"],
        },
        {
            "question": "How do you foster an engineering culture of psychological safety, blameless accountability, and relentless technical excellence?",
            "category": "HR",
            "topic": "Engineering Culture & Organization",
            "expected_focus": ["Encouraging reasoned experimentation", "Blameless root cause investigations", "Rewarding knowledge sharing and systemic fixes"],
        },
        {
            "question": "Describe how you communicate complex, critical systemic vulnerabilities or outages to non-technical executive leadership.",
            "category": "Situational",
            "topic": "Executive Communication",
            "expected_focus": ["Distilling technical jargon into business impact", "Clear recovery and mitigation roadmap", "Confidence and transparent accountability"],
        },
    ],
}


# ==============================================================================
# Helper Functions & DB Interactions
# ==============================================================================
def get_latest_resume_for_user(user_id: str) -> Optional[dict]:
    """Fetches the latest analyzed resume for the user from MongoDB."""
    collection = get_resume_analyses_collection()
    query: Dict[str, Any] = {"user_id": user_id}
    if ObjectId.is_valid(user_id):
        query = {"$or": [{"user_id": user_id}, {"user_id": ObjectId(user_id)}]}
    doc = collection.find_one(query, sort=[("created_at", -1)])
    return doc


def generate_with_gemini(
    target_role: str,
    interview_type: str,
    difficulty: str,
    number_of_questions: int,
    resume_skills: List[str],
) -> Optional[List[dict]]:
    """Calls Gemini API with structured prompt for question generation."""
    if not settings.GEMINI_API_KEY:
        logger.info("GEMINI_API_KEY is not configured; using smart dynamic question engine.")
        return None

    skills_clause = ""
    if resume_skills:
        skills_str = ", ".join(resume_skills)
        skills_clause = f"""
Candidate Verified Resume Skills:
{skills_str}

CRITICAL RESUME PERSONALIZATION REQUIREMENTS:
1. The candidate's resume confirms experience in the above skills.
2. You MUST personalize technical questions directly around these verified skills (e.g. asking for architectural tradeoffs, differences between {skills_str}, and real-world project challenges).
3. Do NOT invent technologies, tools, or past companies that are NOT present in the candidate's resume.
"""
    else:
        skills_clause = """
No resume is available for this candidate. Generate questions strictly tailored to the chosen role, interview type, and difficulty.
"""

    prompt = f"""You are an elite Senior Staff Engineer and Principal Technical & HR Hiring Bar Raiser conducting an interview.
Generate exactly {number_of_questions} realistic, role-specific interview questions.

Configuration:
- Target Job Role: {target_role}
- Interview Type: {interview_type} (Technical, HR, or Mixed)
- Difficulty Level: {difficulty} (Beginner, Intermediate, or Advanced)
- Total Questions Required: {number_of_questions}
{skills_clause}

Requirements:
1. Every question must be directly relevant to '{target_role}' at '{difficulty}' level.
2. For 'Technical': focus on role-specific core concepts, system design, coding patterns, data structures, and database principles.
3. For 'HR': focus on introduction, career trajectory, STAR behavioral stories, teamwork, conflict handling, leadership, and situational questions.
4. For 'Mixed': generate an appropriate, balanced combination of technical and behavioral questions.
5. Realistic questions only. Do NOT invent fake candidate experience.
6. Do NOT include answers, scoring, evaluation, or solution feedback.
7. Provide an array of 2 to 4 key concepts the candidate is expected to cover in 'expected_focus'.

Categories must be selected appropriately from:
- Technical interviews: Technical, Coding, Database, Web Development, Programming, System Design, Problem Solving
- HR interviews: HR, Behavioral, Situational
- Mixed: Combination of the above

Respond ONLY with valid JSON matching this schema:
{{
  "questions": [
    {{
      "question_number": 1,
      "question": "Explain the difference between a list and tuple in Python.",
      "category": "Technical",
      "topic": "Python Fundamentals",
      "difficulty": "{difficulty}",
      "expected_focus": [
        "Mutability",
        "Performance",
        "Use cases"
      ]
    }}
  ]
}}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.3,
        },
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=25)
        if response.status_code == 200:
            res_json = response.json()
            candidates = res_json.get("candidates", [])
            if candidates:
                raw_text = candidates[0]["content"]["parts"][0]["text"].strip()
                # Clean any markdown fences if present
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()

                data = json.loads(raw_text)
                questions = data.get("questions", [])
                if isinstance(questions, list) and len(questions) > 0:
                    cleaned = []
                    for idx, q in enumerate(questions[:number_of_questions], start=1):
                        cleaned.append({
                            "question_number": idx,
                            "question": q.get("question", "").strip(),
                            "category": q.get("category", "Technical" if interview_type != "HR" else "HR"),
                            "topic": q.get("topic", target_role).strip(),
                            "difficulty": q.get("difficulty", difficulty),
                            "expected_focus": q.get("expected_focus", ["Core principles", "Practical application"]),
                        })
                    logger.info(f"Gemini successfully generated {len(cleaned)} interview questions.")
                    return cleaned
        else:
            logger.warning(f"Gemini returned status {response.status_code}: {response.text}")
    except Exception as e:
        logger.warning(f"Gemini API call failed or timed out: {e}")

    return None


def generate_with_smart_fallback(
    target_role: str,
    interview_type: str,
    difficulty: str,
    number_of_questions: int,
    resume_skills: List[str],
) -> List[dict]:
    """Domain-aware question generation engine covering all 8 roles & resume skills."""
    questions: List[dict] = []

    # 1. Resume-specific technical questions if available and type is Technical or Mixed
    if resume_skills and interview_type in ["Technical", "Mixed"]:
        # Skill-specific question templates for verified technologies
        skill_templates = [
            ("In your past projects utilizing {skill}, what was a major architectural tradeoff or performance challenge you faced, and how did you resolve it?",
             "Technical", "{skill} Architecture", ["Practical application of {skill}", "Bottleneck identification", "Impact on project"]),
            ("What is the difference between {skill} and alternative technologies in that domain, and why did you choose it for your project?",
             "Programming", "{skill} Evaluation", ["Tradeoffs and strengths", "Ecosystem integration", "Developer productivity"]),
            ("How do you approach error handling, logging, and automated testing when building services with {skill}?",
             "Problem Solving", "{skill} Testing & Reliability", ["Unit & integration tests", "Fault tolerance", "Observability"]),
            ("Explain how {skill} works in your project when connecting with your database or frontend client.",
             "Web Development", "{skill} Integration", ["Data serialization", "State & connection management", "API performance"]),
        ]

        # Use up to 3 skills
        for idx, skill in enumerate(resume_skills[:3]):
            if len(questions) >= number_of_questions:
                break
            q_tmpl, cat, top_tmpl, focus = skill_templates[idx % len(skill_templates)]
            questions.append({
                "question": q_tmpl.format(skill=skill),
                "category": cat,
                "topic": top_tmpl.format(skill=skill),
                "difficulty": difficulty,
                "expected_focus": focus,
            })

        # Multi-skill integration question if candidate has 2+ skills
        if len(questions) < number_of_questions and len(resume_skills) >= 2:
            s1, s2 = resume_skills[0], resume_skills[1]
            questions.append({
                "question": f"How did you manage data flow, state synchronization, and API contracts between {s1} and {s2} in your project?",
                "category": "System Design",
                "topic": f"{s1} & {s2} Integration",
                "difficulty": difficulty,
                "expected_focus": ["Contract schema validation", "Asynchronous data handling", "Error recovery"],
            })

    # 2. Add Role-specific technical questions if needed
    if interview_type in ["Technical", "Mixed"]:
        role_bank = FALLBACK_QUESTIONS_DB.get(target_role, FALLBACK_QUESTIONS_DB["Software Developer"])
        tech_pool = role_bank.get("Technical", {}).get(difficulty, [])

        # If not enough at this exact difficulty, pull from other difficulties for that same role
        if len(tech_pool) < number_of_questions:
            for diff_level in ["Intermediate", "Beginner", "Advanced"]:
                if diff_level != difficulty:
                    extra = role_bank.get("Technical", {}).get(diff_level, [])
                    for item in extra:
                        if item not in tech_pool:
                            tech_pool.append(item)

        for item in tech_pool:
            if len(questions) >= number_of_questions:
                break
            # Avoid duplicate question text
            if not any(q["question"] == item["question"] for q in questions):
                questions.append({
                    "question": item["question"],
                    "category": item["category"],
                    "topic": item["topic"],
                    "difficulty": difficulty,
                    "expected_focus": item["expected_focus"],
                })

    # 3. Add HR questions if needed
    if interview_type in ["HR", "Mixed"]:
        hr_pool = list(HR_QUESTIONS_DB.get(difficulty, HR_QUESTIONS_DB["Intermediate"]))
        # Also include other difficulty tiers if needed to hit high question count
        for diff_level in ["Intermediate", "Beginner", "Advanced"]:
            if diff_level != difficulty:
                hr_pool.extend(HR_QUESTIONS_DB.get(diff_level, []))

        for item in hr_pool:
            if len(questions) >= number_of_questions:
                break
            if not any(q["question"] == item["question"] for q in questions):
                questions.append({
                    "question": item["question"],
                    "category": item["category"],
                    "topic": item["topic"],
                    "difficulty": difficulty,
                    "expected_focus": item["expected_focus"],
                })

    # 4. Fill remaining questions if count is not reached
    generic_pool = [
        ("Explain how you approach code reviews and maintain clean, scalable architecture standards in a fast-paced environment.", "Programming", "Code Quality", ["Static analysis", "Readability", "Design patterns"]),
        ("How do you identify, reproduce, and diagnose performance bottlenecks or latency spikes in a production environment?", "System Design", "Performance Diagnostics", ["APM profiling", "Resource metrics", "Reproducing in staging"]),
        ("Describe your experience with version control workflows (e.g. Git branching strategies, pull requests, merge conflict resolution).", "Technical", "Version Control", ["Git flow / trunk-based", "Rebase vs merge", "Continuous integration"]),
        ("How do you ensure data integrity, authorization checks, and security compliance in database access layers?", "Database", "Security & Data Integrity", ["SQL injection prevention", "Transactions", "Least privilege access"]),
        ("What is your approach to automated testing (unit, integration, end-to-end) and test-driven development?", "Technical", "Testing Strategy", ["Test pyramid", "Mocking external services", "Coverage metrics"]),
        ("Describe a situation where you had to quickly learn a new technology or framework under tight timelines.", "Behavioral", "Continuous Learning", ["Research methodology", "Building POCs", "Delivering on time"]),
        ("How do you handle technical debt when balancing immediate product deadlines against long-term maintainability?", "Situational", "Technical Debt Management", ["Quantifying impact", "Refactoring in increments", "Team alignment"]),
        ("Describe an experience where a production issue required immediate debugging. What steps did you take?", "Situational", "Incident Response", ["Immediate mitigation", "Root cause analysis", "Post-mortem prevention"]),
    ]

    for q_text, cat, top, focus in generic_pool:
        if len(questions) >= number_of_questions:
            break
        if not any(q["question"] == q_text for q in questions):
            questions.append({
                "question": q_text,
                "category": cat if interview_type != "HR" else "HR",
                "topic": top,
                "difficulty": difficulty,
                "expected_focus": focus,
            })

    # Number each question sequentially
    formatted = []
    for idx, q in enumerate(questions[:number_of_questions], start=1):
        formatted.append({
            "question_number": idx,
            "question": q["question"],
            "category": q["category"],
            "topic": q["topic"],
            "difficulty": q["difficulty"],
            "expected_focus": q["expected_focus"],
        })

    return formatted


def generate_interview_questions(
    target_role: str,
    interview_type: str,
    difficulty: str,
    number_of_questions: int,
    resume_context: Optional[dict] = None,
) -> List[dict]:
    """Primary service entry point to generate role- and resume-aware questions."""
    resume_skills: List[str] = []
    if resume_context and "detected_skills" in resume_context:
        resume_skills = resume_context["detected_skills"]

    # 1. Try Gemini LLM first if API key configured
    questions = generate_with_gemini(
        target_role=target_role,
        interview_type=interview_type,
        difficulty=difficulty,
        number_of_questions=number_of_questions,
        resume_skills=resume_skills,
    )

    # 2. Fallback to smart dynamic generator if Gemini returned None or incomplete
    if not questions or len(questions) != number_of_questions:
        logger.info(f"Using smart question engine for {target_role} ({interview_type}, {difficulty}).")
        questions = generate_with_smart_fallback(
            target_role=target_role,
            interview_type=interview_type,
            difficulty=difficulty,
            number_of_questions=number_of_questions,
            resume_skills=resume_skills,
        )

    return questions


def save_question_set(
    user_id: str,
    target_role: str,
    interview_type: str,
    difficulty: str,
    number_of_questions: int,
    resume_based: bool,
    questions: List[dict],
) -> dict:
    """Stores the generated question set in MongoDB collection 'interview_question_sets'."""
    collection = get_interview_question_sets_collection()
    now = datetime.now(timezone.utc)

    doc = {
        "user_id": user_id,
        "target_role": target_role,
        "interview_type": interview_type,
        "difficulty": difficulty,
        "number_of_questions": number_of_questions,
        "resume_based": resume_based,
        "questions": questions,
        "created_at": now,
    }

    result = collection.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    doc["_id"] = str(result.inserted_id)
    doc["user_id"] = str(user_id)
    return doc


def get_user_question_history(user_id: str) -> List[dict]:
    """Retrieves all past question sets generated by the authenticated user, newest first, with evaluation summaries."""
    collection = get_interview_question_sets_collection()
    eval_col = get_interview_evaluations_collection()
    query: Dict[str, Any] = {"user_id": user_id}
    if ObjectId.is_valid(user_id):
        query = {"$or": [{"user_id": user_id}, {"user_id": ObjectId(user_id)}]}

    cursor = collection.find(query).sort("created_at", -1)

    history = []
    for doc in cursor:
        q_id = doc["_id"]
        # Find evaluations for this set
        evals = list(eval_col.find({"question_set_id": q_id}))
        evaluated_count = len(evals)
        total_q = doc.get("number_of_questions", len(doc.get("questions", []))) or 1

        overall_score = None
        if evaluated_count > 0:
            overall_score = round(sum(e.get("overall_score", 0.0) for e in evals) / evaluated_count, 1)

        completion_rate = round((evaluated_count / total_q) * 100, 1)

        history.append({
            "id": str(doc["_id"]),
            "target_role": doc.get("target_role", "Software Developer"),
            "interview_type": doc.get("interview_type", "Technical"),
            "difficulty": doc.get("difficulty", "Intermediate"),
            "number_of_questions": total_q,
            "resume_based": doc.get("resume_based", False),
            "created_at": doc.get("created_at", datetime.now(timezone.utc)),
            "evaluated_questions": evaluated_count,
            "overall_score": overall_score,
            "completion_rate": completion_rate,
        })
    return history


def get_question_set_by_id(user_id: str, question_set_id: str) -> Optional[dict]:
    """Retrieves a single question set ensuring ownership verification."""
    collection = get_interview_question_sets_collection()
    try:
        oid = ObjectId(question_set_id)
    except Exception:
        return None

    # First check if the question set exists at all
    doc = collection.find_one({"_id": oid})
    if not doc:
        return None

    # Check ownership
    doc_user_id = str(doc.get("user_id", ""))
    if doc_user_id != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to view this question set."
        )

    doc["id"] = str(doc["_id"])
    doc["_id"] = str(doc["_id"])
    doc["user_id"] = doc_user_id
    return doc


# ==============================================================================
# Phase 5: Deterministic Scoring Formulas & AI Answer Evaluation Logic
# ==============================================================================

def calculate_overall_answer_score(
    category: str,
    technical_accuracy: Optional[float],
    relevance: float,
    completeness: float,
    clarity: float,
    communication: float,
) -> float:
    """
    Deterministic scoring formula:
    - Technical/Coding/Systems:
      Technical Accuracy (40%) + Relevance (25%) + Completeness (20%) + Clarity (15%)
    - HR/Behavioral/Situational:
      Relevance (30%) + Communication (30%) + Clarity (20%) + Completeness (20%)
    """
    is_hr = category in ["HR", "Behavioral", "Situational"]
    if is_hr:
        score = (
            (relevance * 0.30)
            + (communication * 0.30)
            + (clarity * 0.20)
            + (completeness * 0.20)
        )
    else:
        tech = technical_accuracy if technical_accuracy is not None else relevance
        score = (
            (tech * 0.40)
            + (relevance * 0.25)
            + (completeness * 0.20)
            + (clarity * 0.15)
        )
    # Clamp between 0.0 and 10.0 and round to 1 decimal place
    return round(max(0.0, min(10.0, score)), 1)


def evaluate_with_gemini(
    target_role: str,
    interview_type: str,
    difficulty: str,
    question: str,
    category: str,
    topic: str,
    expected_focus: List[str],
    candidate_answer: str,
) -> Optional[dict]:
    """Evaluates candidate response via Gemini 1.5 Flash using structured JSON output."""
    if not settings.GEMINI_API_KEY:
        return None

    is_hr = category in ["HR", "Behavioral", "Situational"]
    focus_str = ", ".join(expected_focus) if expected_focus else "Key domain principles and real-world execution"

    prompt = f"""You are a Principal Engineering & HR Technical Interviewer evaluating a candidate's answer for an interview.
Evaluate the candidate's response objectively, rigorously, and constructively.

ROLE: {target_role}
INTERVIEW TYPE: {interview_type}
DIFFICULTY: {difficulty}
CATEGORY: {category}
TOPIC: {topic}
EXPECTED FOCUS POINTS: {focus_str}

QUESTION ASKED:
"{question}"

CANDIDATE'S SUBMITTED ANSWER:
"{candidate_answer}"

EVALUATION INSTRUCTIONS:
1. Do NOT reward mere length or wordiness. A concise, accurate response should receive high scores.
2. Do NOT invent facts or penalize valid alternative solutions.
3. For Technical questions, evaluate technical correctness, conceptual clarity, depth, and practical trade-offs.
4. For HR/Behavioral questions, evaluate relevance, STAR format (Situation, Task, Action, Result), communication, and professionalism.
5. All score dimensions must be integers from 0 to 10.
6. For pure HR questions where technical accuracy is not applicable, set technical_accuracy to null.
7. Provide constructive strengths, specific weaknesses, any omitted key concepts from the expected focus, actionable improvement suggestions, and a clean suggested answer outline.

Return ONLY a valid JSON object matching this schema:
{{
  "technical_accuracy": { "null" if is_hr else "8" },
  "relevance": 8,
  "completeness": 7,
  "clarity": 8,
  "communication": 8,
  "strengths": [
    "Clear explanation of core principles",
    "Addressed real-world trade-offs"
  ],
  "weaknesses": [
    "Omitted performance complexity implications"
  ],
  "missing_points": [
    "Discussion of error boundary handling"
  ],
  "improvement_suggestions": [
    "Mention memory vs CPU trade-offs upfront"
  ],
  "model_answer_outline": "1. Define core mechanism. 2. Compare alternatives. 3. Detail production usage.",
  "summary": "Solid response demonstrating practical understanding with minor gaps in operational edge cases."
}}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.2,
        },
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=25)
        if response.status_code == 200:
            res_json = response.json()
            candidates = res_json.get("candidates", [])
            if candidates:
                raw_text = candidates[0]["content"]["parts"][0]["text"].strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()

                data = json.loads(raw_text)

                # Extract and clamp component scores
                tech = data.get("technical_accuracy")
                tech_score = round(max(0.0, min(10.0, float(tech))), 1) if tech is not None and not is_hr else None
                rel_score = round(max(0.0, min(10.0, float(data.get("relevance", 7.0)))), 1)
                comp_score = round(max(0.0, min(10.0, float(data.get("completeness", 7.0)))), 1)
                clar_score = round(max(0.0, min(10.0, float(data.get("clarity", 7.0)))), 1)
                comm_score = round(max(0.0, min(10.0, float(data.get("communication", 7.0)))), 1)

                overall = calculate_overall_answer_score(
                    category=category,
                    technical_accuracy=tech_score,
                    relevance=rel_score,
                    completeness=comp_score,
                    clarity=clar_score,
                    communication=comm_score,
                )

                return {
                    "overall_score": overall,
                    "technical_accuracy": tech_score,
                    "relevance": rel_score,
                    "completeness": comp_score,
                    "clarity": clar_score,
                    "communication": comm_score,
                    "strengths": data.get("strengths") or ["Accurately identified core problem domain"],
                    "weaknesses": data.get("weaknesses") or ["Could provide more concrete production examples"],
                    "missing_points": data.get("missing_points") or [],
                    "improvement_suggestions": data.get("improvement_suggestions") or ["Structure points using problem-solution-impact"],
                    "model_answer_outline": data.get("model_answer_outline") or f"Address {topic} fundamentals, tradeoffs, and concrete implementation.",
                    "summary": data.get("summary") or "Competent answer addressing primary requirements.",
                }
        else:
            logger.warning(f"Gemini evaluation returned status {response.status_code}: {response.text}")
    except Exception as e:
        logger.warning(f"Gemini evaluation failed or timed out: {e}")

    return None


def evaluate_with_smart_fallback(
    target_role: str,
    interview_type: str,
    difficulty: str,
    question: str,
    category: str,
    topic: str,
    expected_focus: List[str],
    candidate_answer: str,
) -> dict:
    """
    Deterministic domain-calibrated evaluation fallback.
    Analyzes answer content, keyword overlap with expected focus, reasoning structure, and clarity.
    """
    answer_text = candidate_answer.strip()
    words = answer_text.split()
    word_count = len(words)
    lower_ans = answer_text.lower()
    is_hr = category in ["HR", "Behavioral", "Situational"]

    # 1. Analyze focus area keyword coverage
    covered_focus: List[str] = []
    missing_focus: List[str] = []
    for focus_item in expected_focus:
        focus_keywords = re.findall(r"\b\w{3,}\b", focus_item.lower())
        if any(kw in lower_ans for kw in focus_keywords):
            covered_focus.append(focus_item)
        else:
            missing_focus.append(focus_item)

    coverage_ratio = len(covered_focus) / len(expected_focus) if expected_focus else 0.8

    # 2. Structural & Quality Markers
    has_structure = any(term in lower_ans for term in ["first", "second", "because", "tradeoff", "example", "result", "action", "situation", "task", "impact", "solution"])
    has_code_or_tech_terms = any(term in lower_ans for term in ["o(1)", "o(n)", "api", "database", "memory", "cpu", "scale", "performance", "error", "thread", "async", "schema", "test"])
    
    # 3. Base Score Calculations
    if word_count < 10:
        # Extremely brief / minimal answer
        tech_score = 4.0 if not is_hr else None
        rel_score = 5.0
        comp_score = 3.5
        clar_score = 6.0
        comm_score = 5.0
    elif word_count < 30:
        # Brief answer
        base = 6.0 + (coverage_ratio * 2.0)
        tech_score = round(base, 1) if not is_hr else None
        rel_score = round(base + 0.5, 1)
        comp_score = round(5.0 + (coverage_ratio * 2.5), 1)
        clar_score = 7.5
        comm_score = 7.0
    else:
        # Substantive answer
        base = 7.0 + (coverage_ratio * 2.2)
        if has_structure:
            base += 0.4
        if has_code_or_tech_terms and not is_hr:
            base += 0.4
        base = min(9.5, base)

        tech_score = round(base, 1) if not is_hr else None
        rel_score = round(min(9.8, base + 0.3), 1)
        comp_score = round(min(9.5, 6.5 + (coverage_ratio * 3.0)), 1)
        clar_score = round(min(9.6, 7.5 + (0.5 if has_structure else 0.0)), 1)
        comm_score = round(min(9.5, 7.5 + (0.5 if has_structure else 0.0)), 1)

    # 4. Synthesize Constructive Feedback
    strengths = []
    if coverage_ratio >= 0.5 or word_count >= 20:
        strengths.append(f"Demonstrated clear understanding of core concepts in {topic}.")
    if has_structure or is_hr:
        strengths.append("Structured the reasoning logically with identifiable progression.")
    if covered_focus:
        strengths.append(f"Directly addressed key expectation: '{covered_focus[0]}'.")
    if not strengths:
        strengths.append("Provided a direct answer relevant to the interviewer's prompt.")

    weaknesses = []
    if missing_focus:
        weaknesses.append(f"Did not elaborate on key area: '{missing_focus[0]}'.")
    if word_count < 25:
        weaknesses.append("Response is quite concise; could elaborate more on implementation details.")
    if not has_structure and word_count >= 25:
        weaknesses.append("Could benefit from more explicit formatting (e.g. step-by-step or STAR methodology).")
    if not weaknesses:
        weaknesses.append("Could provide additional concrete production scale considerations.")

    missing_points = missing_focus if missing_focus else (["Explicit edge case handling and error recovery"] if not is_hr else ["Measurable quantified outcomes of the actions taken"])

    improvement_suggestions = [
        f"Highlight specific practical experience when discussing {topic}.",
        f"Explicitly mention trade-offs or constraints before presenting your solution.",
    ]
    if is_hr:
        improvement_suggestions.append("Apply the STAR method (Situation, Task, Action, Result) to make behavioral answers memorable.")
    else:
        improvement_suggestions.append("Discuss time and space computational complexity tradeoffs to show engineering maturity.")

    # 5. Suggested Model Outline
    if is_hr:
        model_outline = f"1. Situation: Describe context and stakes. 2. Task: Specific challenge assigned. 3. Action: Your actions and leadership. 4. Result: Quantifiable positive outcome and lessons learned for {topic}."
    else:
        focus_items_str = ", ".join(expected_focus[:3]) if expected_focus else topic
        model_outline = f"1. Direct definition & principles ({topic}). 2. Core mechanics & tradeoffs ({focus_items_str}). 3. Real-world architecture application and failure handling."

    overall_score = calculate_overall_answer_score(
        category=category,
        technical_accuracy=tech_score,
        relevance=rel_score,
        completeness=comp_score,
        clarity=clar_score,
        communication=comm_score,
    )

    summary = f"Solid response addressing {topic} for {target_role} ({difficulty}). Demonstrated good foundational grasp with actionable areas for deepening technical breadth."

    return {
        "overall_score": overall_score,
        "technical_accuracy": tech_score,
        "relevance": rel_score,
        "completeness": comp_score,
        "clarity": clar_score,
        "communication": comm_score,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "missing_points": missing_points,
        "improvement_suggestions": improvement_suggestions,
        "model_answer_outline": model_outline,
        "summary": summary,
    }


def evaluate_interview_answer(
    target_role: str,
    interview_type: str,
    difficulty: str,
    question: str,
    category: str,
    topic: str,
    expected_focus: List[str],
    candidate_answer: str,
) -> dict:
    """Primary service entry point to evaluate candidate answers with Gemini or smart fallback."""
    # 1. Attempt Gemini 1.5 Flash evaluation
    result = evaluate_with_gemini(
        target_role=target_role,
        interview_type=interview_type,
        difficulty=difficulty,
        question=question,
        category=category,
        topic=topic,
        expected_focus=expected_focus,
        candidate_answer=candidate_answer,
    )

    # 2. Use smart fallback if Gemini is not configured, timed out, or returned invalid output
    if not result:
        logger.info(f"Using smart evaluation engine for '{topic}' ({category}, {difficulty}).")
        result = evaluate_with_smart_fallback(
            target_role=target_role,
            interview_type=interview_type,
            difficulty=difficulty,
            question=question,
            category=category,
            topic=topic,
            expected_focus=expected_focus,
            candidate_answer=candidate_answer,
        )

    return result


def save_answer_evaluation(
    user_id: str,
    question_set_id: str,
    question_number: int,
    candidate_answer: str,
    eval_data: dict,
) -> dict:
    """Persists or updates candidate answer evaluation in 'interview_answer_evaluations'."""
    collection = get_interview_evaluations_collection()
    now = datetime.now(timezone.utc)
    q_oid = ObjectId(question_set_id) if ObjectId.is_valid(question_set_id) else question_set_id
    u_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id

    filter_query = {
        "question_set_id": q_oid,
        "question_number": int(question_number),
    }

    update_doc = {
        "$set": {
            "user_id": u_oid,
            "question_set_id": q_oid,
            "question_number": int(question_number),
            "candidate_answer": candidate_answer,
            "overall_score": eval_data["overall_score"],
            "technical_accuracy": eval_data.get("technical_accuracy"),
            "relevance": eval_data["relevance"],
            "completeness": eval_data["completeness"],
            "clarity": eval_data["clarity"],
            "communication": eval_data["communication"],
            "strengths": eval_data.get("strengths", []),
            "weaknesses": eval_data.get("weaknesses", []),
            "missing_points": eval_data.get("missing_points", []),
            "improvement_suggestions": eval_data.get("improvement_suggestions", []),
            "model_answer_outline": eval_data.get("model_answer_outline", ""),
            "summary": eval_data.get("summary", ""),
            "updated_at": now,
        },
        "$setOnInsert": {
            "created_at": now,
        },
    }

    collection.update_one(filter_query, update_doc, upsert=True)
    saved = collection.find_one(filter_query)

    saved["id"] = str(saved["_id"])
    saved["_id"] = str(saved["_id"])
    saved["question_set_id"] = str(saved["question_set_id"])
    saved["user_id"] = str(saved["user_id"])
    return saved


def get_answer_evaluation(
    user_id: str,
    question_set_id: str,
    question_number: int,
) -> Optional[dict]:
    """Retrieves an answer evaluation with strict user ownership verification."""
    # Verify question set ownership first
    qset = get_question_set_by_id(user_id, question_set_id)
    if not qset:
        return None

    collection = get_interview_evaluations_collection()
    q_oid = ObjectId(question_set_id) if ObjectId.is_valid(question_set_id) else question_set_id

    doc = collection.find_one({
        "question_set_id": q_oid,
        "question_number": int(question_number),
    })

    if not doc:
        return None

    # Check ownership
    if str(doc.get("user_id", "")) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to view this evaluation.",
        )

    doc["id"] = str(doc["_id"])
    doc["_id"] = str(doc["_id"])
    doc["question_set_id"] = str(doc["question_set_id"])
    doc["user_id"] = str(doc["user_id"])
    return doc


def get_question_set_evaluations(
    user_id: str,
    question_set_id: str,
) -> List[dict]:
    """Retrieves all evaluated answers for a question set, sorted by question_number."""
    qset = get_question_set_by_id(user_id, question_set_id)
    if not qset:
        return []

    collection = get_interview_evaluations_collection()
    q_oid = ObjectId(question_set_id) if ObjectId.is_valid(question_set_id) else question_set_id

    cursor = collection.find({"question_set_id": q_oid}).sort("question_number", 1)

    evaluations = []
    for doc in cursor:
        doc["id"] = str(doc["_id"])
        doc["_id"] = str(doc["_id"])
        doc["question_set_id"] = str(doc["question_set_id"])
        doc["user_id"] = str(doc["user_id"])
        evaluations.append(doc)

    return evaluations


def generate_final_interview_report(
    user_id: str,
    question_set_id: str,
) -> dict:
    """
    Computes a comprehensive, deterministic final interview report from stored evaluations.
    """
    qset = get_question_set_by_id(user_id, question_set_id)
    if not qset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question set not found.",
        )

    evaluations = get_question_set_evaluations(user_id, question_set_id)

    total_questions = len(qset.get("questions", []))
    evaluated_questions = len(evaluations)
    answered_questions = len([e for e in evaluations if e.get("candidate_answer", "").strip()])
    unanswered_questions = max(0, total_questions - answered_questions)
    completion_rate = round((answered_questions / (total_questions or 1)) * 100, 1)

    if evaluated_questions > 0:
        overall_score = round(sum(e["overall_score"] for e in evaluations) / evaluated_questions, 1)
        score_percentage = round((overall_score / 10.0) * 100, 1)

        tech_evals = [e for e in evaluations if e.get("technical_accuracy") is not None]
        avg_tech = round(sum(e["technical_accuracy"] for e in tech_evals) / len(tech_evals), 1) if tech_evals else None

        avg_rel = round(sum(e["relevance"] for e in evaluations) / evaluated_questions, 1)
        avg_comp = round(sum(e["completeness"] for e in evaluations) / evaluated_questions, 1)
        avg_clar = round(sum(e["clarity"] for e in evaluations) / evaluated_questions, 1)
        avg_comm = round(sum(e["communication"] for e in evaluations) / evaluated_questions, 1)
    else:
        overall_score = 0.0
        score_percentage = 0.0
        avg_tech = None
        avg_rel = 0.0
        avg_comp = 0.0
        avg_clar = 0.0
        avg_comm = 0.0

    # Aggregate strengths, weaknesses, and improvements
    all_strengths = []
    all_weaknesses = []
    all_improvements = []

    for ev in evaluations:
        all_strengths.extend(ev.get("strengths", []))
        all_weaknesses.extend(ev.get("weaknesses", []))
        all_improvements.extend(ev.get("improvement_suggestions", []))

    # Keep top unique items
    def unique_list(items: List[str], max_len: int = 5) -> List[str]:
        seen = set()
        res = []
        for it in items:
            cleaned = it.strip()
            if cleaned and cleaned.lower() not in seen:
                seen.add(cleaned.lower())
                res.append(cleaned)
                if len(res) >= max_len:
                    break
        return res

    strong_areas = unique_list(all_strengths, 5) or ["Solid core comprehension of target role syllabus"]
    weak_areas = unique_list(all_weaknesses, 5) or ["Deepen coverage of production edge cases"]
    top_improvements = unique_list(all_improvements, 5) or ["Provide more concrete metrics and quantifiable outcomes"]

    return {
        "question_set_id": str(qset["id"]),
        "target_role": qset.get("target_role", "Software Developer"),
        "interview_type": qset.get("interview_type", "Technical"),
        "difficulty": qset.get("difficulty", "Intermediate"),
        "total_questions": total_questions,
        "answered_questions": answered_questions,
        "unanswered_questions": unanswered_questions,
        "evaluated_questions": evaluated_questions,
        "completion_rate": completion_rate,
        "overall_score": overall_score,
        "score_percentage": score_percentage,
        "average_technical_accuracy": avg_tech,
        "average_relevance": avg_rel,
        "average_completeness": avg_comp,
        "average_clarity": avg_clar,
        "average_communication": avg_comm,
        "strong_areas": strong_areas,
        "weak_areas": weak_areas,
        "top_improvements": top_improvements,
        "evaluations": evaluations,
        "created_at": datetime.now(timezone.utc),
    }


def get_user_dashboard_metrics(user_id: str) -> dict:
    """Aggregates real candidate dashboard interview scoring statistics."""
    collection = get_interview_evaluations_collection()
    qsets_col = get_interview_question_sets_collection()

    u_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
    query = {"$or": [{"user_id": user_id}, {"user_id": u_oid}]}

    user_qsets = list(qsets_col.find(query))
    total_qsets = len(user_qsets)

    evaluations = list(collection.find(query))
    total_evals = len(evaluations)

    if total_evals > 0:
        avg_score = round(sum(e.get("overall_score", 0.0) for e in evaluations) / total_evals, 1)
        avg_pct = round((avg_score / 10.0) * 100, 1)
        
        # Count question sets where at least 1 question has been evaluated
        evaluated_set_ids = {str(e.get("question_set_id")) for e in evaluations}
        completed_sets = len(evaluated_set_ids)

        return {
            "total_interviews_created": total_qsets,
            "total_evaluations_count": total_evals,
            "completed_interviews_count": completed_sets,
            "average_score": avg_score,
            "average_score_percentage": avg_pct,
            "has_completed_interviews": True,
        }

    return {
        "total_interviews_created": total_qsets,
        "total_evaluations_count": 0,
        "completed_interviews_count": 0,
        "average_score": 0.0,
        "average_score_percentage": 0.0,
        "has_completed_interviews": False,
    }

