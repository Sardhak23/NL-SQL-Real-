"""
Chinook Database Schema Catalog and Sample Natural Language Queries
for the NL-to-SQL Streamlit Enterprise Assistant.

Provides authoritative schema definitions, relationships, table descriptions,
and categorized benchmark prompts aligned with the Chinook SQLite database.
"""

from typing import Dict, List, Any, Optional

# =============================================================================
# 1. Complete Chinook Database Schema Catalog
# =============================================================================

CHINOOK_TABLES: Dict[str, Dict[str, Any]] = {
    "Artist": {
        "description": "Musical artists, bands, composers, and performers.",
        "primary_key": "ArtistId",
        "columns": [
            {"name": "ArtistId", "type": "INTEGER", "description": "Unique artist identifier (Primary Key)", "pk": True},
            {"name": "Name", "type": "NVARCHAR(120)", "description": "Artist or band name", "pk": False}
        ],
        "foreign_keys": []
    },
    "Album": {
        "description": "Music albums, audio collections, and records produced by artists.",
        "primary_key": "AlbumId",
        "columns": [
            {"name": "AlbumId", "type": "INTEGER", "description": "Unique album identifier (Primary Key)", "pk": True},
            {"name": "Title", "type": "NVARCHAR(160)", "description": "Album title", "pk": False},
            {"name": "ArtistId", "type": "INTEGER", "description": "Foreign key referencing Artist.ArtistId", "pk": False}
        ],
        "foreign_keys": [
            {"column": "ArtistId", "references_table": "Artist", "references_column": "ArtistId"}
        ]
    },
    "Track": {
        "description": "Individual digital audio tracks, songs, and media files with duration, size, and pricing.",
        "primary_key": "TrackId",
        "columns": [
            {"name": "TrackId", "type": "INTEGER", "description": "Unique track identifier (Primary Key)", "pk": True},
            {"name": "Name", "type": "NVARCHAR(200)", "description": "Song/track title", "pk": False},
            {"name": "AlbumId", "type": "INTEGER", "description": "Foreign key referencing Album.AlbumId", "pk": False},
            {"name": "MediaTypeId", "type": "INTEGER", "description": "Foreign key referencing MediaType.MediaTypeId", "pk": False},
            {"name": "GenreId", "type": "INTEGER", "description": "Foreign key referencing Genre.GenreId", "pk": False},
            {"name": "Composer", "type": "NVARCHAR(220)", "description": "Track composer(s)", "pk": False},
            {"name": "Milliseconds", "type": "INTEGER", "description": "Track duration in milliseconds", "pk": False},
            {"name": "Bytes", "type": "INTEGER", "description": "File size in bytes", "pk": False},
            {"name": "UnitPrice", "type": "NUMERIC(10,2)", "description": "Retail price per unit in USD", "pk": False}
        ],
        "foreign_keys": [
            {"column": "AlbumId", "references_table": "Album", "references_column": "AlbumId"},
            {"column": "MediaTypeId", "references_table": "MediaType", "references_column": "MediaTypeId"},
            {"column": "GenreId", "references_table": "Genre", "references_column": "GenreId"}
        ]
    },
    "Genre": {
        "description": "Music and media genre classifications (e.g. Rock, Jazz, Metal, Classical, Blues).",
        "primary_key": "GenreId",
        "columns": [
            {"name": "GenreId", "type": "INTEGER", "description": "Unique genre identifier (Primary Key)", "pk": True},
            {"name": "Name", "type": "NVARCHAR(120)", "description": "Genre name", "pk": False}
        ],
        "foreign_keys": []
    },
    "MediaType": {
        "description": "Digital media container encoding types (e.g. MPEG audio file, AAC audio file).",
        "primary_key": "MediaTypeId",
        "columns": [
            {"name": "MediaTypeId", "type": "INTEGER", "description": "Unique media type identifier (Primary Key)", "pk": True},
            {"name": "Name", "type": "NVARCHAR(120)", "description": "Media type description", "pk": False}
        ],
        "foreign_keys": []
    },
    "Invoice": {
        "description": "Customer purchase transactions, invoice totals, billing addresses, and dates.",
        "primary_key": "InvoiceId",
        "columns": [
            {"name": "InvoiceId", "type": "INTEGER", "description": "Unique invoice identifier (Primary Key)", "pk": True},
            {"name": "CustomerId", "type": "INTEGER", "description": "Foreign key referencing Customer.CustomerId", "pk": False},
            {"name": "InvoiceDate", "type": "DATETIME", "description": "Timestamp when the invoice was issued", "pk": False},
            {"name": "BillingAddress", "type": "NVARCHAR(70)", "description": "Billing street address", "pk": False},
            {"name": "BillingCity", "type": "NVARCHAR(40)", "description": "Billing city name", "pk": False},
            {"name": "BillingState", "type": "NVARCHAR(40)", "description": "Billing state/province", "pk": False},
            {"name": "BillingCountry", "type": "NVARCHAR(40)", "description": "Billing country name", "pk": False},
            {"name": "BillingPostalCode", "type": "NVARCHAR(10)", "description": "Billing postal/zip code", "pk": False},
            {"name": "Total", "type": "NUMERIC(10,2)", "description": "Total invoice amount in USD", "pk": False}
        ],
        "foreign_keys": [
            {"column": "CustomerId", "references_table": "Customer", "references_column": "CustomerId"}
        ]
    },
    "InvoiceLine": {
        "description": "Itemized line items of purchased tracks within each customer invoice.",
        "primary_key": "InvoiceLineId",
        "columns": [
            {"name": "InvoiceLineId", "type": "INTEGER", "description": "Unique line item identifier (Primary Key)", "pk": True},
            {"name": "InvoiceId", "type": "INTEGER", "description": "Foreign key referencing Invoice.InvoiceId", "pk": False},
            {"name": "TrackId", "type": "INTEGER", "description": "Foreign key referencing Track.TrackId", "pk": False},
            {"name": "UnitPrice", "type": "NUMERIC(10,2)", "description": "Unit purchase price in USD", "pk": False},
            {"name": "Quantity", "type": "INTEGER", "description": "Number of units purchased", "pk": False}
        ],
        "foreign_keys": [
            {"column": "InvoiceId", "references_table": "Invoice", "references_column": "InvoiceId"},
            {"column": "TrackId", "references_table": "Track", "references_column": "TrackId"}
        ]
    },
    "Customer": {
        "description": "Registered digital media customers with contact information and support assignments.",
        "primary_key": "CustomerId",
        "columns": [
            {"name": "CustomerId", "type": "INTEGER", "description": "Unique customer identifier (Primary Key)", "pk": True},
            {"name": "FirstName", "type": "NVARCHAR(40)", "description": "Customer first name", "pk": False},
            {"name": "LastName", "type": "NVARCHAR(20)", "description": "Customer last name", "pk": False},
            {"name": "Company", "type": "NVARCHAR(80)", "description": "Company name (if business customer)", "pk": False},
            {"name": "Address", "type": "NVARCHAR(70)", "description": "Street address", "pk": False},
            {"name": "City", "type": "NVARCHAR(40)", "description": "City name", "pk": False},
            {"name": "State", "type": "NVARCHAR(40)", "description": "State or region code", "pk": False},
            {"name": "Country", "type": "NVARCHAR(40)", "description": "Country name", "pk": False},
            {"name": "PostalCode", "type": "NVARCHAR(10)", "description": "Postal or ZIP code", "pk": False},
            {"name": "Phone", "type": "NVARCHAR(24)", "description": "Primary phone number", "pk": False},
            {"name": "Fax", "type": "NVARCHAR(24)", "description": "Fax number", "pk": False},
            {"name": "Email", "type": "NVARCHAR(60)", "description": "Customer email address", "pk": False},
            {"name": "SupportRepId", "type": "INTEGER", "description": "Foreign key referencing Employee.EmployeeId", "pk": False}
        ],
        "foreign_keys": [
            {"column": "SupportRepId", "references_table": "Employee", "references_column": "EmployeeId"}
        ]
    },
    "Employee": {
        "description": "Company personnel, management hierarchy, and sales support representatives.",
        "primary_key": "EmployeeId",
        "columns": [
            {"name": "EmployeeId", "type": "INTEGER", "description": "Unique employee identifier (Primary Key)", "pk": True},
            {"name": "LastName", "type": "NVARCHAR(20)", "description": "Employee last name", "pk": False},
            {"name": "FirstName", "type": "NVARCHAR(20)", "description": "Employee first name", "pk": False},
            {"name": "Title", "type": "NVARCHAR(30)", "description": "Job title / role (e.g. Sales Support Agent)", "pk": False},
            {"name": "ReportsTo", "type": "INTEGER", "description": "Foreign key referencing manager's EmployeeId", "pk": False},
            {"name": "BirthDate", "type": "DATETIME", "description": "Date of birth", "pk": False},
            {"name": "HireDate", "type": "DATETIME", "description": "Date of employment hire", "pk": False},
            {"name": "Address", "type": "NVARCHAR(70)", "description": "Home street address", "pk": False},
            {"name": "City", "type": "NVARCHAR(40)", "description": "City of residence", "pk": False},
            {"name": "State", "type": "NVARCHAR(40)", "description": "State or region code", "pk": False},
            {"name": "Country", "type": "NVARCHAR(40)", "description": "Country of residence", "pk": False},
            {"name": "PostalCode", "type": "NVARCHAR(10)", "description": "Postal code", "pk": False},
            {"name": "Phone", "type": "NVARCHAR(24)", "description": "Contact phone number", "pk": False},
            {"name": "Fax", "type": "NVARCHAR(24)", "description": "Fax number", "pk": False},
            {"name": "Email", "type": "NVARCHAR(60)", "description": "Corporate email address", "pk": False}
        ],
        "foreign_keys": [
            {"column": "ReportsTo", "references_table": "Employee", "references_column": "EmployeeId"}
        ]
    },
    "Playlist": {
        "description": "Named curated collections and playlists of music tracks.",
        "primary_key": "PlaylistId",
        "columns": [
            {"name": "PlaylistId", "type": "INTEGER", "description": "Unique playlist identifier (Primary Key)", "pk": True},
            {"name": "Name", "type": "NVARCHAR(120)", "description": "Playlist name", "pk": False}
        ],
        "foreign_keys": []
    },
    "PlaylistTrack": {
        "description": "Junction table mapping many-to-many associations between Playlists and Tracks.",
        "primary_key": "PlaylistId, TrackId",
        "columns": [
            {"name": "PlaylistId", "type": "INTEGER", "description": "Foreign key referencing Playlist.PlaylistId", "pk": True},
            {"name": "TrackId", "type": "INTEGER", "description": "Foreign key referencing Track.TrackId", "pk": True}
        ],
        "foreign_keys": [
            {"column": "PlaylistId", "references_table": "Playlist", "references_column": "PlaylistId"},
            {"column": "TrackId", "references_table": "Track", "references_column": "TrackId"}
        ]
    }
}


# =============================================================================
# 2. Rich Categorized Sample Prompts
# =============================================================================

SAMPLE_PROMPTS: Dict[str, List[str]] = {
    "Music & Catalog": [
        "Who are the top 5 artists by total tracks?",
        "List the top 10 longest songs and their duration in minutes",
        "Which genres have the largest number of tracks in the catalog?",
        "Show all albums by Iron Maiden and their track counts",
        "What are the most popular media types in our catalog?",
        "Which tracks are over 10 minutes long?"
    ],
    "Revenue & Invoices": [
        "What is the total revenue from invoices across all years?",
        "Show annual revenue trend from 2009 to 2013",
        "Break down total sales revenue by music genre",
        "What are the top 5 countries by total invoice revenue?",
        "Show monthly sales for 2012 with total order volume",
        "What is the average order value per invoice?"
    ],
    "Customers & Staff": [
        "Show the top 10 customers by total invoice spend",
        "Which countries have the highest number of registered customers?",
        "Show me all employees who are Sales Support Agents",
        "How many customers does each sales support agent manage?",
        "List customers from the USA who have spent more than $40",
        "Which city has the largest customer concentration?"
    ]
}


# =============================================================================
# 3. Helper Functions
# =============================================================================

def get_schema_summary() -> str:
    """
    Returns a comprehensive, formatted multi-line summary of all Chinook tables,
    columns, primary keys, and foreign key relationships for prompt context or UI display.
    """
    lines: List[str] = [
        "=== Chinook Relational Database Schema Catalog ===",
        "Database contains 11 relational tables describing a digital media store:",
        ""
    ]

    for table_name, meta in CHINOOK_TABLES.items():
        lines.append(f"Table: {table_name} — {meta['description']}")
        lines.append("  Columns:")
        for col in meta["columns"]:
            pk_flag = " [PK]" if col.get("pk") else ""
            lines.append(f"    - {col['name']} ({col['type']}){pk_flag}: {col.get('description', '')}")

        if meta.get("foreign_keys"):
            lines.append("  Foreign Keys:")
            for fk in meta["foreign_keys"]:
                lines.append(f"    - {table_name}.{fk['column']} -> {fk['references_table']}.{fk['references_column']}")
        lines.append("")

    return "\n".join(lines)


def get_table_details(table_name: str) -> Dict[str, Any]:
    """
    Returns metadata for a specific table by name (case-insensitive).
    Returns an empty dict if the table is not found.
    """
    normalized = table_name.strip().lower()
    for name, meta in CHINOOK_TABLES.items():
        if name.lower() == normalized:
            return meta
    return {}


# =============================================================================
# 4. Backward Compatibility Aliases & Helpers
# =============================================================================

# Map of table_name -> list of column dicts for UI schema expanders
SCHEMA_CATALOG: Dict[str, List[Dict[str, str]]] = {
    table_name: [
        {
            "name": col["name"],
            "type": col["type"],
            "description": col.get("description", "")
        }
        for col in meta["columns"]
    ]
    for table_name, meta in CHINOOK_TABLES.items()
}

# Flat list of all sample queries across all categories
SAMPLE_QUERIES: List[str] = [
    query for category_queries in SAMPLE_PROMPTS.values() for query in category_queries
]

# Explicit entity relationship mappings
SCHEMA_RELATIONSHIPS: List[Dict[str, str]] = [
    {"from": "Album.ArtistId", "to": "Artist.ArtistId", "type": "Many-to-One (N:1)"},
    {"from": "Track.AlbumId", "to": "Album.AlbumId", "type": "Many-to-One (N:1)"},
    {"from": "Track.MediaTypeId", "to": "MediaType.MediaTypeId", "type": "Many-to-One (N:1)"},
    {"from": "Track.GenreId", "to": "Genre.GenreId", "type": "Many-to-One (N:1)"},
    {"from": "Invoice.CustomerId", "to": "Customer.CustomerId", "type": "Many-to-One (N:1)"},
    {"from": "InvoiceLine.InvoiceId", "to": "Invoice.InvoiceId", "type": "Many-to-One (N:1)"},
    {"from": "InvoiceLine.TrackId", "to": "Track.TrackId", "type": "Many-to-One (N:1)"},
    {"from": "Customer.SupportRepId", "to": "Employee.EmployeeId", "type": "Many-to-One (N:1)"},
    {"from": "Employee.ReportsTo", "to": "Employee.EmployeeId", "type": "Many-to-One (N:1)"},
    {"from": "PlaylistTrack.PlaylistId", "to": "Playlist.PlaylistId", "type": "Many-to-Many (N:M)"},
    {"from": "PlaylistTrack.TrackId", "to": "Track.TrackId", "type": "Many-to-Many (N:M)"}
]
