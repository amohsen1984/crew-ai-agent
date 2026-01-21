"""JavaScript utilities for Streamlit components using components.html."""

import streamlit.components.v1 as components


def setup_auto_refresh(interval_seconds: int = 30, source: str = "initial-render", job_id: str = None):
    """Set up auto-refresh using JavaScript to click the refresh button.
    
    Args:
        interval_seconds: Refresh interval in seconds (default: 30)
        source: Source of the refresh setup - either 'initial-render' or 'button-press' (default: 'initial-render')
        job_id: Optional job ID to include in query string when reloading
    """
    # Build JavaScript code with job_id handling
    job_id_js = f"'{job_id}'" if job_id else "null"
    job_id_log = job_id if job_id else "none"
    
    components.html(
        f"""
        <script>
        console.log('Setting up auto-refresh every {interval_seconds} seconds ({interval_seconds * 1000} milliseconds) from: {source}');
        const jobId = {job_id_js};
        const intervalMs = {interval_seconds * 1000};
        
        // Clear any existing interval first
        if (typeof window.refreshInterval !== 'undefined') {{
            clearInterval(window.refreshInterval);
        }}
        
        // Function to find and click the refresh button
        function triggerRefresh() {{
            console.log('Triggering refresh with job_id: {job_id_log}');
            
            // Ensure job_id is stored in localStorage
            if (jobId) {{
                localStorage.setItem('processing_job_id', jobId);
            }}
            
            // Try to find the refresh button
            // Streamlit buttons with key='refresh' typically have data-testid ending with 'refresh'
            let refreshButton = null;
            let searchContext = null;
            
            // First try in parent window (Streamlit's main document)
            if (window.parent !== window) {{
                try {{
                    searchContext = window.parent.document;
                    const parentButtons = searchContext.querySelectorAll('button');
                    console.log('Searching in parent window, found', parentButtons.length, 'buttons');
                    
                    parentButtons.forEach((btn, index) => {{
                        const testId = btn.getAttribute('data-testid') || '';
                        const btnText = btn.textContent || btn.innerText || '';
                        const btnId = btn.id || '';
                        
                        // Log first few buttons for debugging
                        if (index < 5) {{
                            console.log(`Parent button ${{index}}: testId="${{testId}}", text="${{btnText}}", id="${{btnId}}"`);
                        }}
                        
                        // Streamlit buttons with key='refresh' have data-testid like 'baseButton-secondary-refresh'
                        // or the button text contains 'Refresh'
                        if (testId.includes('refresh') || btnId === 'refresh' || btnText.includes('Refresh') || btnText.includes('🔄')) {{
                            refreshButton = btn;
                            console.log('Found refresh button in parent:', {{testId, btnText, btnId}});
                        }}
                    }});
                }} catch (e) {{
                    console.log('Cannot access parent window:', e);
                }}
            }}
            
            // Also try in current window
            if (!refreshButton) {{
                searchContext = document;
                const buttons = searchContext.querySelectorAll('button');
                console.log('Searching in current window, found', buttons.length, 'buttons');
                
                buttons.forEach((btn, index) => {{
                    const testId = btn.getAttribute('data-testid') || '';
                    const btnText = btn.textContent || btn.innerText || '';
                    const btnId = btn.id || '';
                    
                    // Log first few buttons for debugging
                    if (index < 5) {{
                        console.log(`Current button ${{index}}: testId="${{testId}}", text="${{btnText}}", id="${{btnId}}"`);
                    }}
                    
                    if (testId.includes('refresh') || btnId === 'refresh' || btnText.includes('Refresh') || btnText.includes('🔄')) {{
                        refreshButton = btn;
                        console.log('Found refresh button in current window:', {{testId, btnText, btnId}});
                    }}
                }});
            }}
            
            if (refreshButton) {{
                console.log('Found refresh button, clicking it');
                refreshButton.click();
            }} else {{
                console.log('Refresh button not found. Available buttons:', 
                    Array.from(searchContext.querySelectorAll('button')).map(btn => ({{
                        testId: btn.getAttribute('data-testid'),
                        text: btn.textContent,
                        id: btn.id
                    }}))
                );
            }}
        }}
        
        // Set up auto-refresh every {interval_seconds} seconds
        window.refreshInterval = setInterval(triggerRefresh, intervalMs);
        </script>
        """,
        height=0,
        width=0,
    )


def clear_auto_refresh():
    """Clear the JavaScript auto-refresh interval."""
    components.html(
        """
        <script>
        if (typeof window.refreshInterval !== 'undefined') {
            clearInterval(window.refreshInterval);
            window.refreshInterval = undefined;
            console.log('Cleared auto-refresh interval');
        }
        </script>
        """,
        height=0,
        width=0,
    )


def load_job_id_from_storage():
    """Load job_id from localStorage and add it to URL query params.
    
    This function reads job_id from localStorage and adds it to the URL
    as a query parameter, then reloads the page so Python can read it.
    """
    components.html(
        """
        <script>
        // Read job_id from localStorage
        const storedJobId = localStorage.getItem('processing_job_id');
        if (storedJobId && !window.location.search.includes('job_id=')) {
            // Add job_id to URL as query parameter
            const url = new URL(window.location);
            url.searchParams.set('job_id', storedJobId);
            window.history.replaceState({}, '', url);
            // Reload to pick up the query param
            // Use current window (cannot access parent due to security restrictions)
            console.log('load_job_id_from_storage: Reloading with job_id in URL');
            window.location.href = url.toString();
        }
        </script>
        """,
        height=0,
        width=0,
    )


def store_job_id_in_storage(job_id: str):
    """Store job_id in localStorage.
    
    Args:
        job_id: The job ID to store
    """
    components.html(
        f"""
        <script>
        localStorage.setItem('processing_job_id', '{job_id}');
        console.log('Stored job_id in localStorage: {job_id}');
        </script>
        """,
        height=0,
        width=0,
    )


def clear_job_id_from_storage(reason: str = "completed"):
    """Clear job_id from localStorage.
    
    Args:
        reason: Reason for clearing - either 'completed' or 'failed'
    """
    components.html(
        f"""
        <script>
        localStorage.removeItem('processing_job_id');
        console.log('Cleared job_id from localStorage ({reason})');
        </script>
        """,
        height=0,
        width=0,
    )



