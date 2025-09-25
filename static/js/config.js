const site_version = "v0.3";

function set_site_status() {
    const footerText = document.getElementById("footer_text");
    footerText.innerHTML = `© 2025 VL_PLAY Games | Download Manager ${site_version}`;
}

document.addEventListener('DOMContentLoaded', set_site_status);