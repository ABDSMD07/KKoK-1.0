import React, { useMemo, useState } from "react";

/* =========================================================
   ICONS
========================================================= */

function DIcon({ name, size = 20 }) {
  const icons = {
    search: (
      <>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-4-4" />
      </>
    ),

    filter: (
      <>
        <path d="M4 6h16" />
        <path d="M7 12h10" />
        <path d="M10 18h4" />
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

    check: (
      <path d="m5 12 4 4L19 6" />
    ),

    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),

    alert: (
      <>
        <path d="M12 3 2.5 20h19z" />
        <path d="M12 9v4" />
        <path d="M12 17h.01" />
      </>
    ),

    calendar: (
      <>
        <rect
          x="3"
          y="5"
          width="18"
          height="16"
          rx="2"
        />
        <path d="M8 3v4" />
        <path d="M16 3v4" />
        <path d="M3 10h18" />
      </>
    ),

    download: (
      <>
        <path d="M12 3v12" />
        <path d="m7 10 5 5 5-5" />
        <path d="M4 20h16" />
      </>
    ),

    eye: (
      <>
        <path d="M2 12s4-6 10-6 10 6 10 6-4 6-10 6S2 12 2 12z" />
        <circle cx="12" cy="12" r="2.5" />
      </>
    ),

    chevronLeft: (
      <path d="m15 18-6-6 6-6" />
    ),

    chevronRight: (
      <path d="m9 18 6-6-6-6" />
    ),
  };

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.9"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {icons[name]}
    </svg>
  );
}

/* =========================================================
   DATA
========================================================= */

const documentRows = [
  {
    id: "MH-04231",
    name: "7/12 Extract",
    type: "7/12 Extract",
    district: "Pune",
    taluka: "Mulshi",
    village: "Hinjewadi",
    status: "Verified",
    date: "10 May 2026",
    uploadedBy: "Ramesh S. Patil",
  },

  {
    id: "MH-01382",
    name: "Sale Deed",
    type: "Sale Deed",
    district: "Nagpur",
    taluka: "Nagpur Rural",
    village: "Mouza Khapri",
    status: "Pending",
    date: "10 May 2026",
    uploadedBy: "Suresh D. More",
  },

  {
    id: "MH-00421",
    name: "8A Document",
    type: "8A Document",
    district: "Thane",
    taluka: "Bhiwandi",
    village: "Bhiwandi",
    status: "Verified",
    date: "09 May 2026",
    uploadedBy: "Amit R. Shinde",
  },

  {
    id: "MH-03120",
    name: "Land Record",
    type: "Land Record",
    district: "Nashik",
    taluka: "Dindori",
    village: "Dindori",
    status: "Pending",
    date: "09 May 2026",
    uploadedBy: "Priya A. Jadhav",
  },

  {
    id: "MH-05029",
    name: "Mutation Entry",
    type: "Mutation Entry",
    district: "Aurangabad",
    taluka: "Paithan",
    village: "Paithan",
    status: "Corrections",
    date: "08 May 2026",
    uploadedBy: "Vijay K. Gaikwad",
  },

  {
    id: "MH-04011",
    name: "Property Card",
    type: "Property Card",
    district: "Kolhapur",
    taluka: "Gaganbawada",
    village: "Gaganbawada",
    status: "Verified",
    date: "07 May 2026",
    uploadedBy: "Sanjay B. Chavan",
  },

  {
    id: "MH-04788",
    name: "Hissa Pahani",
    type: "Hissa Pahani",
    district: "Amravati",
    taluka: "Morshi",
    village: "Morshi",
    status: "Pending",
    date: "07 May 2026",
    uploadedBy: "Mahesh R. Kale",
  },
];

/* =========================================================
   SUMMARY CARD
========================================================= */

function SummaryCard({
  icon,
  theme,
  title,
  value,
  note,
}) {
  return (
    <article className="dx-summary-card">
      <div className={`dx-summary-icon ${theme}`}>
        <DIcon name={icon} size={27} />
      </div>

      <div className="dx-summary-content">
        <span>{title}</span>

        <strong className={theme}>
          {value}
        </strong>

        <small>{note}</small>
      </div>
    </article>
  );
}

/* =========================================================
   DOCUMENTS
========================================================= */

export default function Documents() {
  const [search, setSearch] =
    useState("");

  const [district, setDistrict] =
    useState("All Districts");

  const [taluka, setTaluka] =
    useState("All Talukas");

  const [village, setVillage] =
    useState("All Villages");

  const [
    documentType,
    setDocumentType,
  ] = useState("All Types");

  const [status, setStatus] =
    useState("All Status");

  const [date, setDate] =
    useState("");

  const [page, setPage] =
    useState(1);

  const [applied, setApplied] =
    useState({
      district: "All Districts",
      taluka: "All Talukas",
      village: "All Villages",
      documentType: "All Types",
      status: "All Status",
    });

  /* =========================================================
     FILTERING
  ========================================================= */

  const filteredRows =
    useMemo(() => {
      const query =
        search
          .trim()
          .toLowerCase();

      return documentRows.filter(
        (item) => {
          const matchesSearch =
            !query ||
            Object.values(item)
              .join(" ")
              .toLowerCase()
              .includes(query);

          const matchesDistrict =
            applied.district === "All Districts" ||
            item.district === applied.district;

          const matchesTaluka =
            applied.taluka === "All Talukas" ||
            item.taluka === applied.taluka;

          const matchesVillage =
            applied.village === "All Villages" ||
            item.village === applied.village;

          const matchesType =
            applied.documentType === "All Types" ||
            item.type === applied.documentType;

          const matchesStatus =
            applied.status === "All Status" ||
            item.status === applied.status;

          return (
            matchesSearch &&
            matchesDistrict &&
            matchesTaluka &&
            matchesVillage &&
            matchesType &&
            matchesStatus
          );
        }
      );
    }, [search, applied]);

  function applyFilters() {
    setApplied({
      district,
      taluka,
      village,
      documentType,
      status,
    });

    setPage(1);
  }

  /* =========================================================
     EXPORT
  ========================================================= */

  function exportData() {
    const header = [
      "Document ID",
      "Document Name",
      "Document Type",
      "District",
      "Village",
      "Status",
      "Uploaded On",
      "Uploaded By",
    ];

    const data = [
      header,

      ...filteredRows.map(
        (item) => [
          item.id,
          item.name,
          item.type,
          item.district,
          item.village,
          item.status,
          item.date,
          item.uploadedBy,
        ]
      ),
    ];

    const csv =
      data
        .map((row) =>
          row
            .map(
              (value) =>
                `"${value}"`
            )
            .join(",")
        )
        .join("\n");

    const blob =
      new Blob(
        [csv],
        {
          type:
            "text/csv;charset=utf-8;",
        }
      );

    const url =
      URL.createObjectURL(blob);

    const link =
      document.createElement("a");

    link.href = url;

    link.download =
      "maharashtra-land-documents.csv";

    link.click();

    URL.revokeObjectURL(url);
  }

  return (
    <div className="dx-page">

      {/* =====================================================
          DOCUMENTS + SEARCH
      ===================================================== */}

      <section className="dx-top-row">

        <div className="dx-simple-heading">
          <h1>
            Documents
          </h1>
        </div>

        <div className="dx-main-search">

          <DIcon
            name="search"
            size={20}
          />

          <input
            type="text"
            value={search}
            placeholder="Search documents by name, ID, type, village, or any keyword..."
            onChange={(event) => {
              setSearch(
                event.target.value
              );

              setPage(1);
            }}
          />

          {search && (
            <button
              type="button"
              className="dx-clear"
              onClick={() =>
                setSearch("")
              }
              aria-label="Clear search"
            >
              ×
            </button>
          )}

        </div>

      </section>

      {/* =====================================================
          FILTER - ALWAYS OPEN
      ===================================================== */}

      <section className="dx-filter-static">

        <div className="dx-filter-static-title">

          <DIcon
            name="filter"
            size={19}
          />

          <strong>
            Filter
          </strong>

        </div>

        <div className="dx-filter-static-grid">

          {/* DISTRICT */}

          <label>
            <span>
              District
            </span>

            <select
              value={district}
              onChange={(event) =>
                setDistrict(
                  event.target.value
                )
              }
            >
              <option>
                All Districts
              </option>

              <option>Pune</option>
              <option>Nagpur</option>
              <option>Thane</option>
              <option>Nashik</option>
              <option>
                Aurangabad
              </option>
              <option>
                Kolhapur
              </option>
              <option>
                Amravati
              </option>
            </select>
          </label>

          {/* TALUKA */}

          <label>
            <span>
              Taluka
            </span>

            <select
              value={taluka}
              onChange={(event) =>
                setTaluka(
                  event.target.value
                )
              }
            >
              <option>
                All Talukas
              </option>

              <option>
                Mulshi
              </option>

              <option>
                Nagpur Rural
              </option>

              <option>
                Bhiwandi
              </option>

              <option>
                Dindori
              </option>

              <option>
                Paithan
              </option>

              <option>
                Gaganbawada
              </option>

              <option>
                Morshi
              </option>
            </select>
          </label>

          {/* VILLAGE */}

          <label>
            <span>
              Village
            </span>

            <select
              value={village}
              onChange={(event) =>
                setVillage(
                  event.target.value
                )
              }
            >
              <option>
                All Villages
              </option>

              <option>
                Hinjewadi
              </option>

              <option>
                Mouza Khapri
              </option>

              <option>
                Bhiwandi
              </option>

              <option>
                Dindori
              </option>

              <option>
                Paithan
              </option>

              <option>
                Gaganbawada
              </option>

              <option>
                Morshi
              </option>
            </select>
          </label>

          {/* DOCUMENT TYPE */}

          <label>
            <span>
              Document Type
            </span>

            <select
              value={documentType}
              onChange={(event) =>
                setDocumentType(
                  event.target.value
                )
              }
            >
              <option>
                All Types
              </option>

              <option>
                7/12 Extract
              </option>

              <option>
                Sale Deed
              </option>

              <option>
                8A Document
              </option>

              <option>
                Land Record
              </option>

              <option>
                Mutation Entry
              </option>

              <option>
                Property Card
              </option>

              <option>
                Hissa Pahani
              </option>
            </select>
          </label>

          {/* STATUS */}

          <label>
            <span>
              Status
            </span>

            <select
              value={status}
              onChange={(event) =>
                setStatus(
                  event.target.value
                )
              }
            >
              <option>
                All Status
              </option>

              <option>
                Verified
              </option>

              <option>
                Pending
              </option>

              <option>
                Corrections
              </option>
            </select>
          </label>

          {/* DATE RANGE */}

          <label>
            <span>
              Date Range
            </span>

            <div className="dx-filter-static-date">

              <DIcon
                name="calendar"
                size={17}
              />

              <input
                type="date"
                value={date}
                onChange={(event) =>
                  setDate(
                    event.target.value
                  )
                }
              />

            </div>

          </label>

        </div>

        {/* APPLY FILTER */}

        <div className="dx-filter-static-action">

          <button
            type="button"
            onClick={applyFilters}
          >
            <DIcon
              name="search"
              size={16}
            />

            Apply Filter
          </button>

        </div>

      </section>

      {/* =====================================================
          KPI CARDS
      ===================================================== */}

      <section className="dx-summary-grid">

        <SummaryCard
          icon="document"
          theme="blue"
          title="Total Documents"
          value="18,420"
          note="Across all districts"
        />

        <SummaryCard
          icon="check"
          theme="green"
          title="Verified"
          value="14,286"
          note="77.6% of total"
        />

        <SummaryCard
          icon="clock"
          theme="orange"
          title="Pending Review"
          value="2,914"
          note="15.8% of total"
        />

        <SummaryCard
          icon="alert"
          theme="red"
          title="Corrections"
          value="1,220"
          note="6.6% of total"
        />

      </section>

      {/* =====================================================
          DOCUMENT LIST
      ===================================================== */}

      <section className="dx-document-list">

        <header className="dx-list-header">

          <div className="dx-list-heading">

            <span>
              <DIcon
                name="document"
                size={20}
              />
            </span>

            <strong>
              Documents List
            </strong>

          </div>

          <button
            type="button"
            className="dx-export"
            onClick={exportData}
          >
            <DIcon
              name="download"
              size={17}
            />

            Export
          </button>

        </header>

        {/* TABLE */}

        <div className="dx-table-scroll">

          <table className="dx-table">

            <thead>
              <tr>
                <th>
                  Document ID
                </th>

                <th>
                  Document Name
                </th>

                <th>
                  Document Type
                </th>

                <th>
                  District
                </th>

                <th>
                  Village
                </th>

                <th>
                  Status
                </th>

                <th>
                  Uploaded On
                </th>

                <th>
                  Uploaded By
                </th>

                <th>
                  Action
                </th>
              </tr>
            </thead>

            <tbody>

              {filteredRows.length > 0 ? (
                filteredRows.map(
                  (item) => (
                    <tr key={item.id}>

                      <td>
                        <strong className="dx-id">
                          {item.id}
                        </strong>
                      </td>

                      <td>
                        {item.name}
                      </td>

                      <td>
                        {item.type}
                      </td>

                      <td>
                        {item.district}
                      </td>

                      <td>
                        {item.village}
                      </td>

                      <td>
                        <span
                          className={`dx-status ${item.status
                            .toLowerCase()
                            .replace(
                              /\s+/g,
                              "-"
                            )}`}
                        >
                          {item.status}
                        </span>
                      </td>

                      <td>
                        {item.date}
                      </td>

                      <td>
                        {item.uploadedBy}
                      </td>

                      <td>
                        <button
                          type="button"
                          className="dx-view"
                          title="View Document"
                        >
                          <DIcon
                            name="eye"
                            size={18}
                          />
                        </button>
                      </td>

                    </tr>
                  )
                )
              ) : (
                <tr>
                  <td
                    colSpan={9}
                    className="dx-no-results"
                  >
                    No documents found for selected filters.
                  </td>
                </tr>
              )}

            </tbody>

          </table>

        </div>

        {/* ===================================================
            TABLE FOOTER
        =================================================== */}

        <footer className="dx-table-footer">

          <span>
            Showing 1 to{" "}
            {filteredRows.length} of
            18,420 documents
          </span>

          <div className="dx-pagination">

            <button
              type="button"
              className="dx-page-arrow"
              aria-label="Previous page"
              onClick={() =>
                setPage(
                  (current) =>
                    Math.max(
                      1,
                      current - 1
                    )
                )
              }
            >
              <DIcon
                name="chevronLeft"
                size={18}
              />
            </button>

            {[1, 2, 3].map(
              (number) => (
                <button
                  type="button"
                  key={number}
                  className={
                    page === number
                      ? "active"
                      : ""
                  }
                  onClick={() =>
                    setPage(number)
                  }
                >
                  {number}
                </button>
              )
            )}

            <span className="dx-page-dots">
              ...
            </span>

            <button
              type="button"
              className={
                page === 2632
                  ? "active"
                  : ""
              }
              onClick={() =>
                setPage(2632)
              }
            >
              2632
            </button>

            <button
              type="button"
              className="dx-page-arrow"
              aria-label="Next page"
              onClick={() =>
                setPage(
                  (current) =>
                    Math.min(
                      2632,
                      current + 1
                    )
                )
              }
            >
              <DIcon
                name="chevronRight"
                size={18}
              />
            </button>

          </div>

        </footer>

      </section>

    </div>
  );
}