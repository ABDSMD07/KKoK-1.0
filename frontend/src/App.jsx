import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import "./App.css";
import Documents from "./Documents";

import hero1 from "./assets/hero1.png";
import hero2 from "./assets/hero2.jpeg";
import hero3 from "./assets/hero3.jpeg";
import hero4 from "./assets/hero4.jpeg";
import hero5 from "./assets/hero5.jpeg";

const API_URL = "http://127.0.0.1:8000";

const heroImages = [
  hero1,
  hero2,
  hero3,
  hero4,
  hero5,
];

/* =========================================================
   ICONS
========================================================= */

function Icon({ name, size = 20 }) {
  const icons = {
    overview: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </>
    ),

    document: (
      <>
        <path d="M6 2h8l4 4v16H6z" />
        <path d="M14 2v5h5" />
        <path d="M9 12h6" />
        <path d="M9 16h6" />
      </>
    ),

    upload: (
      <>
        <path d="M12 16V4" />
        <path d="m7 9 5-5 5 5" />
        <path d="M4 15v5h16v-5" />
      </>
    ),

    verify: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="m8 12 3 3 6-7" />
      </>
    ),

    report: (
      <>
        <path d="M5 20V11" />
        <path d="M12 20V4" />
        <path d="M19 20v-6" />
        <path d="M3 20h18" />
      </>
    ),

    bell: (
      <>
        <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
        <path d="M14 21h-4" />
      </>
    ),

    menu: (
      <>
        <path d="M4 6h16" />
        <path d="M4 12h16" />
        <path d="M4 18h16" />
      </>
    ),

    chevron: (
      <path d="m7 9 5 5 5-5" />
    ),

    activity: (
      <path d="M3 12h4l2-5 4 10 2-5h6" />
    ),

    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),

    retry: (
      <>
        <path d="M3 12a9 9 0 1 1 3 6.7" />
        <path d="M3 17v-5h5" />
      </>
    ),

    alert: (
      <>
        <path d="M12 3 2.5 20h19z" />
        <path d="M12 9v4" />
        <path d="M12 17h.01" />
      </>
    ),

    cloudUpload: (
      <>
        <path d="M16 16l-4-4-4 4" />
        <path d="M12 12v9" />
        <path d="M20.4 17.5A5 5 0 0 0 18 8.2 7 7 0 0 0 4.3 9.8 4.5 4.5 0 0 0 5.5 18H8" />
      </>
    ),
  };

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {icons[name]}
    </svg>
  );
}

/* =========================================================
   HEADER
========================================================= */

function Header({ onToggle }) {
  const [profileOpen, setProfileOpen] =
    useState(false);

  return (
    <header className="gov-header">
      <div className="header-left">
        <button
          type="button"
          className="menu-toggle"
          onClick={onToggle}
          aria-label="Toggle sidebar"
        >
          <Icon name="menu" size={21} />
        </button>

        <div className="gov-seal">
          <div className="seal-inner">
            म
          </div>
        </div>

        <div className="gov-name">
          <strong>
            महाराष्ट्र शासन
          </strong>

          <span>
            Government of Maharashtra
          </span>
        </div>

        <div className="header-divider" />

        <div className="portal-name">
          <strong>
            महाभूमि अभिलेख महाराष्ट्र
          </strong>

          <span>
            Intelligent Land Records Management System
          </span>
        </div>
      </div>

      <div className="header-tools">
        <button
          type="button"
          className="language-btn"
        >
          मराठी

          <span />

          English
        </button>

        <button
          type="button"
          className="bell-btn"
          aria-label="Notifications"
        >
          <Icon
            name="bell"
            size={20}
          />

          <b>1</b>
        </button>

        <div className="header-profile">
          <div className="avatar">
            SK
          </div>

          <div className="user-detail">
            <strong>
              S.K. Sharma
            </strong>

            <span>
              Admin
            </span>
          </div>

          <button
            type="button"
            className="profile-chevron"
            aria-label="Profile menu"
            onClick={() =>
              setProfileOpen(
                (current) =>
                  !current
              )
            }
          >
            <Icon
              name="chevron"
              size={15}
            />
          </button>

          {profileOpen && (
            <div className="profile-dropdown">
              <div className="profile-dropdown-user">
                <div className="profile-dropdown-avatar">
                  SK
                </div>

                <div>
                  <strong>
                    S.K. Sharma
                  </strong>

                  <span>
                    Administrator
                  </span>
                </div>
              </div>

              <button type="button">
                My Profile
              </button>

              <button type="button">
                Account Settings
              </button>

              <button
                type="button"
                className="logout-btn"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

/* =========================================================
   SIDEBAR
========================================================= */

const navItems = [
  ["Overview", "overview"],
  ["Documents", "document"],
  ["Regional Progress", "report"],
  ["Error Management", "alert"],
];

function Sidebar({
  activePage,
  setActivePage,
}) {
  return (
    <aside className="sidebar">
      <nav>
        {navItems.map(
          ([name, icon]) => (
            <button
              type="button"
              key={name}
              title={name}
              className={`nav-item ${
                activePage === name
                  ? "active"
                  : ""
              }`}
              onClick={() =>
                setActivePage(name)
              }
            >
              <Icon
                name={icon}
                size={20}
              />

              <span>
                {name}
              </span>
            </button>
          )
        )}
      </nav>

      <div className="sidebar-footer">
        <i />

        <div>
          <strong>
            Government Secure Portal
          </strong>

          <span>
            Land Records Department
          </span>
        </div>
      </div>
    </aside>
  );
}

/* =========================================================
   HERO
========================================================= */

function HeroSlider() {
  const [
    currentImage,
    setCurrentImage,
  ] = useState(0);

  useEffect(() => {
    const timer =
      window.setInterval(
        () => {
          setCurrentImage(
            (current) =>
              (current + 1) %
              heroImages.length
          );
        },
        2000
      );

    return () => {
      window.clearInterval(
        timer
      );
    };
  }, []);

  return (
    <section className="hero">
      {heroImages.map(
        (image, index) => (
          <img
            key={image}
            src={image}
            alt={`Maharashtra Land Banner ${
              index + 1
            }`}
            className={`hero-slide ${
              currentImage === index
                ? "active"
                : ""
            }`}
          />
        )
      )}
    </section>
  );
}

/* =========================================================
   KPI
========================================================= */

function StatCard({ item }) {
  return (
    <article
      className={`stat-card ${item.color}`}
    >
      <div
        className={`stat-icon ${item.color}`}
      >
        <Icon
          name={item.icon}
          size={25}
        />
      </div>

      <div className="stat-copy">
        <span>
          {item.title}
        </span>

        <strong>
          {item.value}
        </strong>

        <small>
          {item.note}
        </small>
      </div>
    </article>
  );
}

/* =========================================================
   UPLOAD
========================================================= */

function UploadDocuments({
  onUpload,
  uploading,
  message,
  messageType,
}) {
  const inputRef =
    useRef(null);

  const [
    dragging,
    setDragging,
  ] = useState(false);

  function processFile(file) {
    if (
      !file ||
      uploading
    ) {
      return;
    }

    const validTypes = [
      "application/pdf",
      "image/png",
      "image/jpeg",
    ];

    const validExtension =
      /\.(pdf|png|jpe?g)$/i.test(
        file.name
      );

    if (
      !validTypes.includes(
        file.type
      ) &&
      !validExtension
    ) {
      window.alert(
        "Please select a PDF, PNG, JPG or JPEG file."
      );

      return;
    }

    if (
      file.size >
      25 * 1024 * 1024
    ) {
      window.alert(
        "Maximum file size is 25 MB."
      );

      return;
    }

    onUpload(file);
  }

  return (
    <section className="upload-card">
      <div
        className={`upload-dropzone ${
          dragging
            ? "upload-dragging"
            : ""
        }`}
        onDragOver={(event) => {
          event.preventDefault();

          if (!uploading) {
            setDragging(true);
          }
        }}
        onDragLeave={() =>
          setDragging(false)
        }
        onDrop={(event) => {
          event.preventDefault();

          setDragging(false);

          processFile(
            event.dataTransfer
              .files?.[0]
          );
        }}
      >
        <div className="cloud-circle">
          {uploading ? (
            <span className="upload-spinner" />
          ) : (
            <Icon
              name="cloudUpload"
              size={27}
            />
          )}
        </div>

        <h2>
          {uploading
            ? "Uploading Document..."
            : "Upload Land Documents"}
        </h2>

        <p>
          {uploading
            ? "Saving document and starting intelligent processing"
            : "Upload files for verification and intelligent processing"}
        </p>

        <button
          type="button"
          className="upload-button"
          disabled={uploading}
          onClick={() =>
            inputRef.current?.click()
          }
        >
          <Icon
            name="upload"
            size={16}
          />

          {uploading
            ? "Uploading..."
            : "Upload File"}
        </button>

        <small>
          PDF, PNG, JPG or JPEG • Maximum file size 25 MB
        </small>

        {message && (
          <div
            className={`upload-result ${messageType}`}
          >
            {message}
          </div>
        )}

        <input
          ref={inputRef}
          type="file"
          hidden
          disabled={uploading}
          accept=".pdf,.png,.jpg,.jpeg"
          onChange={(event) => {
            processFile(
              event.target
                .files?.[0]
            );

            event.target.value =
              "";
          }}
        />
      </div>
    </section>
  );
}

/* =========================================================
   STATUS PILL
========================================================= */

function StatusPill({
  document,
  onClick,
}) {
  if (
    document.status ===
    "Verified"
  ) {
    return (
      <button
        type="button"
        className="status-pill verified"
        onClick={onClick}
      >
        <Icon
          name="verify"
          size={18}
        />

        Verified
      </button>
    );
  }

  if (
    document.status ===
    "Under Review"
  ) {
    return (
      <button
        type="button"
        className="status-pill review"
        onClick={onClick}
      >
        <Icon
          name="clock"
          size={18}
        />

        Under Review
      </button>
    );
  }

  return (
    <button
      type="button"
      className="status-pill processing"
      onClick={onClick}
    >
      <Icon
        name="activity"
        size={19}
      />

      Processing
    </button>
  );
}

/* =========================================================
   DOCUMENT PIPELINE
========================================================= */

function getDocumentPipeline(
  backendStatus
) {
  const steps = [
    {
      name: "Upload",
      label:
        "Document received",
      state: "done",
    },

    {
      name: "CV",
      label: "Pending",
      state: "pending",
    },

    {
      name: "OCR",
      label: "Pending",
      state: "pending",
    },

    {
      name: "Extraction",
      label: "Pending",
      state: "pending",
    },

    {
      name: "Validation",
      label: "Pending",
      state: "pending",
    },

    {
      name: "Verification",
      label: "Pending",
      state: "pending",
    },
  ];

  if (
    backendStatus === "Queued" ||
    backendStatus === "Uploaded"
  ) {
    steps[0] = {
      ...steps[0],

      label:
        backendStatus ===
        "Queued"
          ? "Queued for processing"
          : "Document received",
    };

    return steps;
  }

  if (
    backendStatus ===
    "CV Processing"
  ) {
    steps[1] = {
      ...steps[1],

      state: "active",

      label:
        "Processing...",
    };

    return steps;
  }

  if (
    backendStatus ===
    "CV Failed"
  ) {
    steps[1] = {
      ...steps[1],

      state: "failed",

      label:
        "Processing failed",
    };

    return steps;
  }

  steps[1] = {
    ...steps[1],

    state: "done",

    label: "Completed",
  };

  if (
    backendStatus ===
    "CV Completed"
  ) {
    return steps;
  }

  if (
    backendStatus ===
    "OCR Processing"
  ) {
    steps[2] = {
      ...steps[2],

      state: "active",

      label:
        "Reading document...",
    };

    return steps;
  }

  if (
    backendStatus ===
    "OCR Failed"
  ) {
    steps[2] = {
      ...steps[2],

      state: "failed",

      label:
        "Recognition failed",
    };

    return steps;
  }

  if (
    backendStatus ===
    "OCR Completed"
  ) {
    steps[2] = {
      ...steps[2],

      state: "done",

      label: "Completed",
    };

    return steps;
  }

  if (
    backendStatus ===
    "Verified"
  ) {
    return steps.map(
      (step) => ({
        ...step,

        state: "done",

        label:
          "Completed",
      })
    );
  }

  return steps;
}

/* =========================================================
   PROCESSING POPUP
========================================================= */

function ProcessingPopup({
  document,
  onClose,
  onRetry,
  retrying,
  retryError,
}) {
  if (!document) {
    return null;
  }

  const pipeline =
    getDocumentPipeline(
      document.backendStatus
    );

  const retryAvailable =
    document.backendStatus ===
      "CV Failed" ||
    document.backendStatus ===
      "OCR Failed";

  return (
    <div
      className="popup-backdrop"
      onMouseDown={onClose}
    >
      <section
        className="processing-popup"
        onMouseDown={(event) =>
          event.stopPropagation()
        }
      >
        <header className="popup-header">
          <div>
            <h3>
              Processing Progress
            </h3>

            <p>
              {
                document.backendStatus
              }
            </p>
          </div>

          <span
            className={`process-indicator ${
              retryAvailable
                ? "failed"
                : ""
            }`}
          />

          <button
            type="button"
            className="popup-close"
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </header>

        <div className="stage-list">
          {pipeline.map(
            (
              step,
              index
            ) => {
              let state =
                step.state;

              if (
                state === "done"
              ) {
                state =
                  "complete";
              }

              if (
                state === "active"
              ) {
                state =
                  "current";
              }

              if (
                state === "failed"
              ) {
                state =
                  "failure";
              }

              return (
                <div
                  key={
                    step.name
                  }
                  className={`stage ${state}`}
                >
                  <div className="stage-marker">
                    <span>
                      {state ===
                      "complete"
                        ? "✓"
                        : state ===
                          "failure"
                        ? "!"
                        : state ===
                          "current"
                        ? "•"
                        : ""}
                    </span>

                    {index <
                      pipeline.length -
                        1 && (
                      <i />
                    )}
                  </div>

                  <div className="stage-copy">
                    <strong>
                      {
                        step.name
                      }
                    </strong>

                    <p>
                      {
                        step.label
                      }
                    </p>
                  </div>

                  <span
                    className={`stage-state ${state}`}
                  >
                    {state ===
                    "complete"
                      ? "Completed"
                      : state ===
                        "failure"
                      ? "Failed"
                      : state ===
                        "current"
                      ? "Processing"
                      : "Pending"}
                  </span>
                </div>
              );
            }
          )}
        </div>

        {retryError && (
          <div className="popup-retry-error">
            <Icon
              name="alert"
              size={16}
            />

            <span>
              {retryError}
            </span>
          </div>
        )}

        {retryAvailable && (
          <button
            type="button"
            className="retry-button"
            disabled={retrying}
            onClick={() =>
              onRetry(
                document.id
              )
            }
          >
            <Icon
              name="retry"
              size={20}
            />

            {retrying
              ? "Retrying..."
              : "Retry Processing"}
          </button>
        )}
      </section>
    </div>
  );
}

/* =========================================================
   RECENT DOCUMENTS
========================================================= */

function RecentDocuments({
  documents,
  loading,
  onRetry,
  retryingId,
  retryError,
}) {
  const [
    selectedDocumentId,
    setSelectedDocumentId,
  ] = useState(null);

  const [
    visibleCount,
    setVisibleCount,
  ] = useState(5);

  const selectedDocument =
    documents.find(
      (document) =>
        document.id ===
        selectedDocumentId
    ) || null;

  const visibleDocuments =
    documents.slice(
      0,
      visibleCount
    );

  const hasMore =
    visibleCount <
    documents.length;

  return (
    <>
      <section className="recent-documents">
        <div className="recent-header">
          <div>
            <h2>
              Recent Documents
            </h2>

            <p>
              Latest documents entering the system
            </p>
          </div>
        </div>

        <div className="recent-table-wrap">
          <table className="recent-table">
            <colgroup>
              <col className="recent-col-id" />

              <col className="recent-col-file" />

              <col className="recent-col-status" />

              <col className="recent-col-confidence" />

              <col className="recent-col-uploaded" />
            </colgroup>

            <thead>
              <tr>
                <th>
                  DOCUMENT ID
                </th>

                <th>
                  FILE NAME
                </th>

                <th>
                  STATUS
                </th>

                <th>
                  CONFIDENCE
                </th>

                <th>
                  UPLOADED ON
                </th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td
                    colSpan={5}
                    className="recent-empty"
                  >
                    Loading documents...
                  </td>
                </tr>
              ) : documents.length ===
                0 ? (
                <tr>
                  <td
                    colSpan={5}
                    className="recent-empty"
                  >
                    No documents yet.
                  </td>
                </tr>
              ) : (
                visibleDocuments.map(
                  (
                    document,
                    index
                  ) => (
                    <tr
                      key={
                        document.id
                      }
                      className={
                        index === 0
                          ? "selected-row"
                          : ""
                      }
                    >
                      <td className="recent-id-cell">
                        <strong className="doc-id">
                          {
                            document.id
                          }
                        </strong>
                      </td>

                      <td className="recent-file-cell">
                        <div className="file-name">
                          <Icon
                            name="document"
                            size={21}
                          />

                          <span>
                            {
                              document.name
                            }
                          </span>
                        </div>
                      </td>

                      <td className="recent-status-cell">
                        <StatusPill
                          document={
                            document
                          }
                          onClick={() =>
                            setSelectedDocumentId(
                              document.id
                            )
                          }
                        />
                      </td>

                      <td className="recent-confidence-cell">
                        <strong className="confidence-number">
                          {
                            document.confidence
                          }
                        </strong>
                      </td>

                      <td className="recent-upload-cell">
                        <div className="upload-date">
                          <span>
                            {
                              document.date
                            }
                          </span>

                          <span>
                            {
                              document.time
                            }
                          </span>
                        </div>
                      </td>
                    </tr>
                  )
                )
              )}
            </tbody>
          </table>
        </div>

        {hasMore && (
          <div className="documents-footer">
            <button
              type="button"
              className="view-all-bottom"
              onClick={() =>
                setVisibleCount(
                  (current) =>
                    Math.min(
                      current + 5,
                      documents.length
                    )
                )
              }
            >
              View all
            </button>
          </div>
        )}
      </section>

      <ProcessingPopup
        document={
          selectedDocument
        }
        onClose={() =>
          setSelectedDocumentId(
            null
          )
        }
        onRetry={
          onRetry
        }
        retrying={
          retryingId ===
          selectedDocumentId
        }
        retryError={
          selectedDocument
            ? retryError
            : ""
        }
      />
    </>
  );
}

/* =========================================================
   APP
========================================================= */

function App() {
  const [
    menuOpen,
    setMenuOpen,
  ] = useState(true);

  const [
    activePage,
    setActivePage,
  ] = useState(
    "Overview"
  );

  const [
    documents,
    setDocuments,
  ] = useState([]);

  const [
    loadingDocuments,
    setLoadingDocuments,
  ] = useState(true);

  const [
    uploading,
    setUploading,
  ] = useState(false);

  const [
    uploadMessage,
    setUploadMessage,
  ] = useState("");

  const [
    uploadMessageType,
    setUploadMessageType,
  ] = useState(
    "success"
  );

  const [
    retryingId,
    setRetryingId,
  ] = useState(null);

  const [
    retryError,
    setRetryError,
  ] = useState("");

  /* =====================================================
     DATE
  ===================================================== */

  const formatDateParts =
    useCallback(
      (dateString) => {
        if (!dateString) {
          return {
            date: "—",
            time: "",
          };
        }

        const date =
          new Date(
            dateString
          );

        if (
          Number.isNaN(
            date.getTime()
          )
        ) {
          return {
            date: "—",
            time: "",
          };
        }

        return {
          date:
            date.toLocaleDateString(
              "en-IN",
              {
                timeZone:
                  "Asia/Kolkata",

                day:
                  "2-digit",

                month:
                  "short",

                year:
                  "numeric",
              }
            ),

          time:
            date.toLocaleTimeString(
              "en-IN",
              {
                timeZone:
                  "Asia/Kolkata",

                hour:
                  "2-digit",

                minute:
                  "2-digit",

                hour12:
                  true,
              }
            ),
        };
      },
      []
    );

  /* =====================================================
     NORMALIZE BACKEND STATUS
  ===================================================== */

  const normalizeStatus =
    useCallback(
      (status) => {
        if (
          status ===
          "Verified"
        ) {
          return "Verified";
        }

        if (
          status ===
            "CV Failed" ||
          status ===
            "OCR Failed" ||
          status ===
            "Under Review"
        ) {
          return "Under Review";
        }

        return "Processing";
      },
      []
    );

  /* =====================================================
     FORMAT BACKEND DOCUMENT
  ===================================================== */

  const formatDocument =
    useCallback(
      (document) => {
        const formattedDate =
          formatDateParts(
            document.uploaded_at
          );

        return {
          id:
            document.document_id,

          name:
            document.filename,

          backendStatus:
            document.status ||
            "Queued",

          status:
            normalizeStatus(
              document.status
            ),

          confidence:
            document.confidence ||
            "—",

          date:
            formattedDate.date,

          time:
            formattedDate.time,
        };
      },
      [
        formatDateParts,
        normalizeStatus,
      ]
    );

  /* =====================================================
     LOAD REAL DOCUMENTS
  ===================================================== */

  const loadDocuments =
    useCallback(
      async (
        showLoader = false
      ) => {
        if (showLoader) {
          setLoadingDocuments(
            true
          );
        }

        try {
          const response =
            await fetch(
              `${API_URL}/api/documents`,
              {
                cache:
                  "no-store",
              }
            );

          if (!response.ok) {
            throw new Error(
              "Could not load documents"
            );
          }

          const data =
            await response.json();

          const rows =
            Array.isArray(data)
              ? data
              : [];

          setDocuments(
            rows.map(
              formatDocument
            )
          );
        } catch (error) {
          console.error(
            "Error loading documents:",
            error
          );
        } finally {
          setLoadingDocuments(
            false
          );
        }
      },
      [
        formatDocument,
      ]
    );

  /* =====================================================
     INITIAL LOAD
  ===================================================== */

  useEffect(() => {
    loadDocuments(true);
  }, [
    loadDocuments,
  ]);

  /* =====================================================
     LIVE POLLING
  ===================================================== */

  useEffect(() => {
    const processing =
      documents.some(
        (document) =>
          [
            "Queued",
            "Uploaded",
            "CV Processing",
            "CV Completed",
            "OCR Processing",
          ].includes(
            document.backendStatus
          )
      );

    if (!processing) {
      return undefined;
    }

    const timer =
      window.setInterval(
        () => {
          loadDocuments(
            false
          );
        },
        1500
      );

    return () => {
      window.clearInterval(
        timer
      );
    };
  }, [
    documents,
    loadDocuments,
  ]);

  /* =====================================================
     REAL UPLOAD
  ===================================================== */

  const handleUpload =
    async (file) => {
      if (
        !file ||
        uploading
      ) {
        return;
      }

      setUploading(true);

      setUploadMessage("");

      setUploadMessageType(
        "success"
      );

      const formData =
        new FormData();

      formData.append(
        "file",
        file
      );

      try {
        const response =
          await fetch(
            `${API_URL}/api/documents/upload`,
            {
              method:
                "POST",

              body:
                formData,
            }
          );

        let data = {};

        try {
          data =
            await response.json();
        } catch {
          data = {};
        }

        if (!response.ok) {
          throw new Error(
            data.detail ||
              "Upload failed"
          );
        }

        const newDocument =
          formatDocument(
            data
          );

        setDocuments(
          (
            currentDocuments
          ) => [
            newDocument,

            ...currentDocuments.filter(
              (document) =>
                document.id !==
                newDocument.id
            ),
          ]
        );

        setUploadMessageType(
          "success"
        );

        setUploadMessage(
          `Uploaded successfully — ${data.document_id}. Processing queued.`
        );

        await loadDocuments(
          false
        );
      } catch (error) {
        console.error(
          "Upload error:",
          error
        );

        setUploadMessageType(
          "error"
        );

        setUploadMessage(
          `Upload failed — ${
            error.message ||
            "Unknown error"
          }`
        );
      } finally {
        setUploading(
          false
        );
      }
    };

  /* =====================================================
     REAL RETRY
  ===================================================== */

  const handleRetry =
    async (documentId) => {
      if (retryingId) {
        return;
      }

      setRetryingId(
        documentId
      );

      setRetryError("");

      try {
        const response =
          await fetch(
            `${API_URL}/api/documents/${documentId}/retry`,
            {
              method:
                "POST",
            }
          );

        let data = {};

        try {
          data =
            await response.json();
        } catch {
          data = {};
        }

        if (!response.ok) {
          throw new Error(
            data.detail ||
              `Retry failed (${response.status})`
          );
        }

        await loadDocuments(
          false
        );
      } catch (error) {
        console.error(
          "Retry error:",
          error
        );

        setRetryError(
          error.message ||
            "Retry failed."
        );
      } finally {
        setRetryingId(
          null
        );
      }
    };

  /* =====================================================
     REAL KPI COUNTS
  ===================================================== */

  const totalDocuments =
    documents.length;

  const processingCount =
    documents.filter(
      (document) =>
        document.status ===
        "Processing"
    ).length;

  const reviewCount =
    documents.filter(
      (document) =>
        document.status ===
        "Under Review"
    ).length;

  const verifiedCount =
    documents.filter(
      (document) =>
        document.status ===
        "Verified"
    ).length;

  const verifiedPercentage =
    totalDocuments > 0
      ? (
          (verifiedCount /
            totalDocuments) *
          100
        ).toFixed(1)
      : "0.0";

  const stats = [
    {
      title:
        "Total Records",

      value:
        totalDocuments.toLocaleString(
          "en-IN"
        ),

      note:
        `Total Records: ${totalDocuments.toLocaleString(
          "en-IN"
        )}`,

      icon:
        "document",

      color:
        "blue",
    },

    {
      title:
        "Processing",

      value:
        processingCount.toLocaleString(
          "en-IN"
        ),

      note:
        `Currently processing: ${processingCount.toLocaleString(
          "en-IN"
        )}`,

      icon:
        "activity",

      color:
        "blue",
    },

    {
      title:
        "Pending Verification",

      value:
        reviewCount.toLocaleString(
          "en-IN"
        ),

      note:
        `Requires attention: ${reviewCount.toLocaleString(
          "en-IN"
        )}`,

      icon:
        "clock",

      color:
        "red",
    },

    {
      title:
        "Validated Records",

      value:
        verifiedCount.toLocaleString(
          "en-IN"
        ),

      note:
        `${verifiedPercentage}% of total`,

      icon:
        "verify",

      color:
        "green",
    },
  ];

  return (
    <div
      className={`app ${
        menuOpen
          ? ""
          : "sidebar-collapsed"
      }`}
    >
      <Header
        onToggle={() =>
          setMenuOpen(
            (current) =>
              !current
          )
        }
      />

      <div className="layout">
        <Sidebar
          activePage={
            activePage
          }
          setActivePage={
            setActivePage
          }
        />

        <main className="main">

          {/* =================================================
              OVERVIEW
          ================================================= */}

          {activePage ===
            "Overview" && (
            <>
              <HeroSlider />

              <section className="stats-grid">
                {stats.map(
                  (item) => (
                    <StatCard
                      key={
                        item.title
                      }
                      item={
                        item
                      }
                    />
                  )
                )}
              </section>

              <UploadDocuments
                onUpload={
                  handleUpload
                }
                uploading={
                  uploading
                }
                message={
                  uploadMessage
                }
                messageType={
                  uploadMessageType
                }
              />

              <RecentDocuments
                documents={
                  documents
                }
                loading={
                  loadingDocuments
                }
                onRetry={
                  handleRetry
                }
                retryingId={
                  retryingId
                }
                retryError={
                  retryError
                }
              />
            </>
          )}

          {/* =================================================
              DOCUMENTS
              SAME REAL BACKEND DATA AS OVERVIEW
          ================================================= */}

          {activePage ===
            "Documents" && (
            <Documents
              documents={
                documents
              }
              loading={
                loadingDocuments
              }
              onRefresh={() =>
                loadDocuments(
                  false
                )
              }
            />
          )}

          {/* =================================================
              REGIONAL PROGRESS
          ================================================= */}

          {activePage ===
            "Regional Progress" && (
            <div className="module-placeholder">
              <Icon
                name="report"
                size={38}
              />

              <h2>
                Regional Progress
              </h2>

              <p>
                Regional Progress page content will be available here.
              </p>
            </div>
          )}

          {/* =================================================
              ERROR MANAGEMENT
          ================================================= */}

          {activePage ===
            "Error Management" && (
            <div className="module-placeholder">
              <Icon
                name="alert"
                size={38}
              />

              <h2>
                Error Management
              </h2>

              <p>
                Error Management page content will be available here.
              </p>
            </div>
          )}

        </main>
      </div>
    </div>
  );
}

export default App;