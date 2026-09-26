#!/usr/bin/python3
"""
KUTTY HACKER - Phone Number OSINT Tool
Version: 3.0 (Full OSINT Suite)
"""

import sys
import os
import json
import asyncio
import urllib.parse
from typing import Dict, Any, Optional

import requests
import aiohttp
import phonenumbers
from phonenumbers import (
    parse,
    is_valid_number,
    format_number,
    PhoneNumberFormat,
    PhoneNumberType,
    number_type,
    geocoder,
    carrier,
    timezone,
)
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

BANNER = """[bold red]
 ██╗  ██╗██╗   ██╗████████╗████████╗██╗   ██╗
 ██║ ██╔╝██║   ██║╚══██╔══╝╚══██╔══╝██║   ██║
 █████╔╝ ██║   ██║   ██║      ██║   ██║   ██║
 ██╔═██╗ ██║   ██║   ██║      ██║   ╚██╗ ██╔╝
 ██║  ██╗╚██████╔╝   ██║      ██║    ╚████╔╝
 ╚═╝  ╚═╝ ╚═════╝    ╚═╝      ╚═╝     ╚═══╝[/bold red]
[bold cyan]      KUTTY HACKER - Phone OSINT Suite[/bold cyan]
"""

# Type mapping for phonenumbers
TYPE_MAP = {
    PhoneNumberType.MOBILE: "Mobile",
    PhoneNumberType.FIXED_LINE: "Fixed Line",
    PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed Line or Mobile",
    PhoneNumberType.TOLL_FREE: "Toll Free",
    PhoneNumberType.PREMIUM_RATE: "Premium Rate",
    PhoneNumberType.VOIP: "VoIP",
    PhoneNumberType.PERSONAL_NUMBER: "Personal Number",
    PhoneNumberType.PAGER: "Pager",
    PhoneNumberType.UAN: "UAN",
    PhoneNumberType.VOICEMAIL: "Voicemail",
}

def parse_basic_metadata(raw_num: str) -> Optional[Dict[str, Any]]:
    """Extracts offline metadata using Google's libphonenumber."""
    try:
        parsed = parse(raw_num)
        if not is_valid_number(parsed):
            console.print("[bold red][!] Invalid phone number format.[/bold red]")
            return None

        tz_tuple = timezone.time_zones_for_number(parsed)
        ntype = number_type(parsed)

        return {
            "e164": format_number(parsed, PhoneNumberFormat.E164),
            "international": format_number(parsed, PhoneNumberFormat.INTERNATIONAL),
            "national": format_number(parsed, PhoneNumberFormat.NATIONAL),
            "country_code": parsed.country_code,
            "national_number": parsed.national_number,
            "country": geocoder.country_name_for_number(parsed, "en") or "Unknown",
            "region": geocoder.description_for_number(parsed, "en") or "Unknown",
            "timezones": list(tz_tuple) if tz_tuple else ["Unknown"],
            "carrier": carrier.name_for_number(parsed, "en") or "Unknown",
            "line_type": TYPE_MAP.get(ntype, "Unknown"),
        }
    except Exception as e:
        console.print(f"[bold red][!] Parsing error: {e}[/bold red]")
        return None

def generate_search_dorks(e164_num: str, national_num: str) -> Dict[str, str]:
    """Generates direct search engine links and dorks for public leaks."""
    query_exact = f'"{e164_num}" OR "{national_num}"'
    encoded_query = urllib.parse.quote(query_exact)

    return {
        "Google Dork Search": f"https://www.google.com/search?q={encoded_query}",
        "Bing Search": f"https://www.bing.com/search?q={encoded_query}",
        "DuckDuckGo Search": f"https://duckduckgo.com/?q={encoded_query}",
        "Truecaller Search": f"https://www.truecaller.com/search/in/{e164_num.replace('+', '')}",
        "Sync.me Search": f"https://sync.me/search/?number={e164_num.replace('+', '')}",
    }

def generate_messaging_links(e164_num: str) -> Dict[str, str]:
    """Generates direct protocol launch links for messaging applications."""
    clean_num = e164_num.replace("+", "")
    return {
        "WhatsApp Direct Chat": f"https://wa.me/{clean_num}",
        "Telegram Direct Chat": f"https://t.me/+{clean_num}",
        "Viber Direct URI": f"viber://chat?number=%2B{clean_num}",
    }

async def check_endpoint(session: aiohttp.ClientSession, name: str, url: str) -> tuple[str, str]:
    """Asynchronously pings a web target endpoint."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        async with session.get(url, headers=headers, timeout=8, allow_redirects=True) as resp:
            if resp.status == 200:
                return name, "Reachable (HTTP 200)"
            return name, f"HTTP {resp.status}"
    except Exception:
        return name, "Unreachable / Timeout"

async def batch_probe_services(e164_num: str) -> Dict[str, str]:
    """Probes web target endpoints asynchronously."""
    clean = e164_num.replace("+", "")
    targets = {
        "WhatsApp Web": f"https://wa.me/{clean}",
        "Telegram Web": f"https://t.me/+{clean}",
    }

    async with aiohttp.ClientSession() as session:
        tasks = [check_endpoint(session, name, url) for name, url in targets.items()]
        results = await asyncio.gather(*tasks)
        return dict(results)

def fetch_numverify_data(e164_num: str, api_key: str) -> Optional[Dict[str, Any]]:
    """Queries the NumVerify API if an API key is provided."""
    try:
        url = f"http://apilayer.net/api/validate?access_key={api_key}&number={e164_num}&format=1"
        res = requests.get(url, timeout=10).json()
        if res.get("valid"):
            return {
                "Valid": res.get("valid"),
                "Local Format": res.get("local_format"),
                "International Format": res.get("international_format"),
                "Country Name": res.get("country_name"),
                "Location": res.get("location"),
                "Carrier": res.get("carrier"),
                "Line Type": res.get("line_type"),
            }
    except Exception as e:
        console.print(f"[bold red][!] NumVerify API Error: {e}[/bold red]")
    return None

def main():
    console.print(BANNER)

    raw_input = console.input("[bold green]Enter Phone Number (+CountryCode Number): [/bold green]").strip()
    if not raw_input.startswith("+"):
        console.print("[bold red][!] Error: Input must start with '+' and country code (e.g. +14155552671).[/bold red]")
        sys.exit(1)

    # 1. Local Metadata Parse
    basic_data = parse_basic_metadata(raw_input)
    if not basic_data:
        sys.exit(1)

    # Display Metadata
    table = Table(title="Base Phone Metadata", style="bold cyan")
    table.add_column("Attribute", style="yellow")
    table.add_column("Value", style="white")

    for key, val in basic_data.items():
        val_str = ", ".join(val) if isinstance(val, list) else str(val)
        table.add_column if False else None
        table.add_row(key.replace("_", " ").title(), val_str)

    console.print(table)

    # 2. Generate Direct Platform URIs
    msg_links = generate_messaging_links(basic_data["e164"])
    msg_table = Table(title="Direct Messenger Launch URIs", style="bold green")
    msg_table.add_column("Platform", style="yellow")
    msg_table.add_column("Direct URI", style="blue")
    for name, link in msg_links.items():
        msg_table.add_row(name, link)
    console.print(msg_table)

    # 3. Search Engine & Dork Links
    dork_links = generate_search_dorks(basic_data["e164"], str(basic_data["national_number"]))
    dork_table = Table(title="Search Engine & OSINT Footprint Links", style="bold magenta")
    dork_table.add_column("Source", style="yellow")
    dork_table.add_column("Query Link", style="blue")
    for source, url in dork_links.items():
        dork_table.add_row(source, url)
    console.print(dork_table)

    # 4. Async Service Probing
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        progress.add_task(description="Probing public platforms...", total=None)
        probe_results = asyncio.run(batch_probe_services(basic_data["e164"]))

    probe_table = Table(title="Endpoint Accessibility Probe", style="bold yellow")
    probe_table.add_column("Endpoint", style="cyan")
    probe_table.add_column("HTTP Status", style="white")
    for site, status in probe_results.items():
        probe_table.add_row(site, status)
    console.print(probe_table)

    # 5. Optional External APIs
    numverify_data = None
    api_key = console.input("\n[bold green]Enter NumVerify API Key (Press Enter to skip): [/bold green]").strip()
    if api_key:
        numverify_data = fetch_numverify_data(basic_data["e164"], api_key)
        if numverify_data:
            nv_table = Table(title="NumVerify API Results", style="bold blue")
            nv_table.add_column("Field", style="yellow")
            nv_table.add_column("Data", style="white")
            for k, v in numverify_data.items():
                nv_table.add_row(k, str(v))
            console.print(nv_table)

    # 6. Save JSON Report
    save_choice = console.input("\n[bold yellow]Save full OSINT report to file? (y/N): [/bold yellow]").strip().lower()
    if save_choice == "y":
        report = {
            "metadata": basic_data,
            "messaging_uris": msg_links,
            "dork_urls": dork_links,
            "endpoint_probes": probe_results,
            "numverify_api": numverify_data,
        }
        filename = f"report_{basic_data['e164'].replace('+', '')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4)
        console.print(f"[bold green][+] Full report successfully written to {filename}[/bold green]")

if __name__ == "__main__":
    main()
