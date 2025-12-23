import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import requests
import json
from typing import Optional, Dict, Any
import sys
from groq import Groq

class LeetCodeAgent:
    def __init__(self, groq_api_key: str = None):
        self.driver = None
        self.session = requests.Session()
        self.is_logged_in = False
        self.groq_client = None
        self.max_retries = 3
        self.retry_delay = 5
        
        if groq_api_key:
            self.groq_client = Groq(api_key=groq_api_key)
        
        self.setup_logging()
        self.setup_headers()
        
    def setup_headers(self):
        """Setup headers for requests"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('leetcode_agent.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def init_driver(self):
        """Initialize Chrome driver with optimal settings"""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--start-maximized')
            options.add_argument('--disable-gpu')
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.logger.info("Chrome driver initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize driver: {e}")
            return False

    def manual_login(self):
        """Wait for user to manually login"""
        try:
            if not self.driver:
                if not self.init_driver():
                    return False

            self.logger.info("Navigating to LeetCode...")
            self.driver.get("https://leetcode.com")
            time.sleep(2)
            
            print("\n" + "="*60)
            print("🤖 MANUAL LOGIN REQUIRED")
            print("="*60)
            print("Please manually login to LeetCode in the browser window.")
            print("Steps:")
            print("1. Click 'Sign In' in the top right")
            print("2. Enter your credentials")
            print("3. Complete any CAPTCHA if required")
            print("4. Wait until you see the main LeetCode dashboard")
            print("5. Return here and press Enter to continue...")
            print("="*60 + "\n")
            
            input("Press Enter after you have successfully logged in...")
            
            # Verify login was successful
            try:
                # Check if we're on a logged-in page
                current_url = self.driver.current_url
                if "leetcode.com" in current_url and "accounts/login" not in current_url:
                    self.is_logged_in = True
                    self.logger.info("Manual login successful!")
                    return True
                else:
                    # Try to check for user avatar or logged-in elements
                    logged_in_selectors = [
                        "//img[contains(@class, 'avatar')]",
                        "//a[contains(@href, '/subscriptions/')]",
                        "//span[contains(text(), 'Problems')]",
                        "//div[contains(@class, 'navbar-left')]//a[contains(@href, '/problemset/')]"
                    ]
                    
                    for selector in logged_in_selectors:
                        try:
                            element = self.driver.find_element(By.XPATH, selector)
                            if element.is_displayed():
                                self.is_logged_in = True
                                self.logger.info("Manual login successful!")
                                return True
                        except:
                            continue
                    
                    self.logger.warning("Could not verify login automatically, but continuing...")
                    self.is_logged_in = True
                    return True
                    
            except Exception as e:
                self.logger.warning(f"Login verification failed: {e}, but continuing...")
                self.is_logged_in = True
                return True
                
        except Exception as e:
            self.logger.error(f"Manual login process failed: {e}")
            return False

    def ensure_python_language(self):
        """Ensure Python is selected as the programming language"""
        try:
            self.logger.info("Ensuring Python language is selected...")
            
            # Check if Python is already selected by looking for active Python indicator
            python_indicators = [
                "//button[contains(@class, 'rounded') and contains(., 'Python')]",
                "//div[contains(@class, 'text-text-primary') and contains(text(), 'Python')]"
            ]
            
            for indicator in python_indicators:
                try:
                    element = self.driver.find_element(By.XPATH, indicator)
                    if element.is_displayed():
                        self.logger.info("Python is already selected")
                        return True
                except:
                    continue
            
            # If Python is not selected, try to select it
            self.logger.info("Python not selected, attempting to select...")
            return self._select_python_language()
            
        except Exception as e:
            self.logger.error(f"Failed to ensure Python language: {e}")
            return False

    def _select_python_language(self):
        """Select Python as the programming language"""
        try:
            # Find and click language selector button
            language_button_selectors = [
                "//button[contains(@class, 'rounded') and .//div[contains(text(), 'Python')]]",
                "//button[contains(@class, 'rounded')]",
                "//div[contains(@class, 'relative')]//button"
            ]
            
            language_button = None
            for selector in language_button_selectors:
                try:
                    language_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if language_button:
                        break
                except:
                    continue
            
            if not language_button:
                self.logger.warning("Could not find language selector button")
                return False
            
            # Click the language button to open dropdown
            self.driver.execute_script("arguments[0].click();", language_button)
            time.sleep(2)
            
            # Now find and click Python option
            python_option_selectors = [
                "//div[contains(@class, 'cursor-pointer') and .//div[contains(text(), 'Python')]]",
                "//div[contains(text(), 'Python') and contains(@class, 'text-text-primary')]",
                "//div[contains(text(), 'Python')]"
            ]
            
            python_option = None
            for selector in python_option_selectors:
                try:
                    python_option = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if python_option:
                        break
                except:
                    continue
            
            if not python_option:
                self.logger.warning("Could not find Python option in dropdown")
                return False
            
            # Click the Python option
            self.driver.execute_script("arguments[0].click();", python_option)
            time.sleep(3)
            
            self.logger.info("✅ Python language selected successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to select Python language: {e}")
            return False

    def extract_problem_statement(self, problem_url: str) -> Dict[str, Any]:
        """Extract complete problem statement with retry mechanism"""
        for attempt in range(3):
            try:
                self.logger.info(f"Attempt {attempt + 1}: Extracting problem statement...")
                
                if attempt > 0:
                    # Refresh page and wait
                    self.driver.refresh()
                    time.sleep(5)
                
                self.logger.info(f"Navigating to problem: {problem_url}")
                self.driver.get(problem_url)
                
                # Wait for page to load completely
                time.sleep(5)
                
                # Ensure Python language is selected
                self.ensure_python_language()
                
                problem_data = {
                    "title": "",
                    "description": "",
                    "examples": [],
                    "constraints": "",
                    "difficulty": "",
                    "url": problem_url,
                    "code_template": ""
                }

                # Extract title with multiple attempts
                title = self._extract_title()
                problem_data["title"] = title

                # Extract description
                description = self._extract_description()
                problem_data["description"] = description

                # Extract difficulty
                difficulty = self._extract_difficulty()
                problem_data["difficulty"] = difficulty

                # Extract code template
                code_template = self._extract_code_template()
                problem_data["code_template"] = code_template

                self.logger.info(f"Extracted problem: {problem_data['title']} ({problem_data['difficulty']})")
                self.logger.info(f"Description length: {len(problem_data['description'])} characters")
                
                # Validate we have sufficient data
                if (problem_data['description'] and len(problem_data['description']) > 100 and 
                    problem_data['title'] and problem_data['title'] != "Unknown Problem"):
                    return problem_data
                else:
                    self.logger.warning(f"Insufficient data extracted on attempt {attempt + 1}")
                    continue
                    
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < 2:  # Don't sleep after last attempt
                    time.sleep(3)
        
        self.logger.error("All attempts to extract problem statement failed")
        return self._fallback_extraction()

    def _extract_title(self) -> str:
        """Extract problem title"""
        title_selectors = [
            "//div[contains(@data-cy, 'question-title')]//a",
            "//div[contains(@class, 'flex')]//span[contains(@class, 'text-label')]",
            "//a[contains(@class, 'no-underline')]//span",
            "//h1//a",
            "//h1",
            "//title"
        ]
        
        for selector in title_selectors:
            try:
                element = self.driver.find_element(By.XPATH, selector)
                text = element.text.strip()
                if text and len(text) > 5:
                    return text
            except:
                continue
        return "Unknown Problem"

    def _extract_description(self) -> str:
        """Extract problem description"""
        # First try to find and expand any hidden content
        self._expand_hidden_content()
        
        desc_selectors = [
            "//div[contains(@class, 'content__u3I1')]",
            "//div[contains(@class, 'question-content__JfgR')]",
            "//div[contains(@class, 'description')]",
            "//div[contains(@data-cy, 'description')]",
            "//div[contains(@class, 'elfjS')]",
            "//div[contains(@class, 'xFUwe')]",
            "//div[contains(@class, '_1l1MA')]",
            "//div[@role='main']//div[contains(@class, 'content')]"
        ]
        
        for selector in desc_selectors:
            try:
                element = self.driver.find_element(By.XPATH, selector)
                text = element.text.strip()
                if text and len(text) > 200:
                    return text
            except:
                continue
        return ""

    def _expand_hidden_content(self):
        """Click any buttons that might expand hidden content"""
        expand_buttons = [
            "//button[contains(text(), 'Expand')]",
            "//button[contains(text(), 'Show')]",
            "//button[contains(text(), 'View')]",
            "//button[contains(@class, 'expand')]",
            "//button[contains(@class, 'show-more')]"
        ]
        
        for button_selector in expand_buttons:
            try:
                button = self.driver.find_element(By.XPATH, button_selector)
                self.driver.execute_script("arguments[0].click();", button)
                time.sleep(1)
                self.logger.info(f"Clicked expand button: {button_selector}")
            except:
                continue

    def _extract_difficulty(self) -> str:
        """Extract problem difficulty"""
        diff_selectors = [
            "//div[contains(@class, 'difficulty-label')]",
            "//span[contains(@class, 'difficulty')]",
            "//div[contains(@data-difficulty)]",
            "//span[contains(@class, 'text-difficulty')]"
        ]
        
        for selector in diff_selectors:
            try:
                element = self.driver.find_element(By.XPATH, selector)
                text = element.text.strip()
                if text and text in ['Easy', 'Medium', 'Hard']:
                    return text
            except:
                continue
        return "Unknown"

    def _extract_code_template(self) -> str:
        """Extract code template from editor"""
        try:
            # Wait for code editor to load
            time.sleep(3)
            
            # Try multiple code editor selectors
            editor_selectors = [
                "//div[contains(@class, 'CodeMirror')]",
                "//div[contains(@class, 'monaco-editor')]",
                "//textarea[contains(@class, 'inputarea')]",
                "//div[contains(@class, 'view-lines')]"
            ]
            
            for selector in editor_selectors:
                try:
                    editor = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    code_text = editor.text
                    if code_text and len(code_text) > 10:
                        return code_text
                except:
                    continue
                    
            # Try to get text from code lines
            code_lines = self.driver.find_elements(By.CLASS_NAME, "CodeMirror-line")
            if code_lines:
                return "\n".join([line.text for line in code_lines])
                
        except Exception as e:
            self.logger.warning(f"Could not extract code template: {e}")
            
        return ""

    def _fallback_extraction(self) -> Dict[str, Any]:
        """Fallback extraction when all else fails"""
        try:
            # Get whatever text we can from the page
            body = self.driver.find_element(By.TAG_NAME, "body")
            full_text = body.text[:3000]
            
            return {
                "title": self.driver.title.replace(" - LeetCode", "").strip(),
                "description": full_text,
                "examples": [],
                "constraints": "",
                "difficulty": "Unknown",
                "code_template": "",
                "url": self.driver.current_url
            }
        except Exception as e:
            self.logger.error(f"Fallback extraction failed: {e}")
            return {
                "title": "Unknown Problem",
                "description": "Could not extract problem description",
                "examples": [],
                "constraints": "",
                "difficulty": "Unknown",
                "code_template": "",
                "url": self.driver.current_url
            }

    def call_groq_for_solution(self, problem_data: Dict[str, Any], attempt: int = 1) -> str:
        """Call Groq API to generate optimized Python solution with feedback"""
        if not self.groq_client:
            self.logger.error("Groq client not initialized")
            return self._mock_llm_call(problem_data)
        
        try:
            # Prepare prompt with feedback if this is a retry
            feedback_note = f"\n\nNOTE: This is attempt {attempt}. " if attempt > 1 else ""
            
            prompt = f"""
            PROBLEM TITLE: {problem_data['title']}
            DIFFICULTY: {problem_data['difficulty']}
            {feedback_note}
            PROBLEM DESCRIPTION:
            {problem_data['description'][:4000]}

            CODE TEMPLATE (if available):
            {problem_data.get('code_template', 'None provided')}

            Provide ONLY the complete runnable Python code solution. No explanations, no comments, just the code.
            Make sure the code is correct and handles all edge cases.
            """
            
            self.logger.info(f"Calling Groq API for solution generation (attempt {attempt})...")
            
            response = self.groq_client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {
                        "role": "system",
                        "content": "You are senior coding developer your work is to solve a problem always answer only code no answer nothing just code in python. Return only Python code without any explanations, comments, or markdown formatting. Make sure the code is correct and complete."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2048,
                top_p=0.95,
                stream=False
            )
            
            solution_code = response.choices[0].message.content.strip()
            
            # Clean up the response
            solution_code = self._clean_code_response(solution_code)
            
            self.logger.info("Groq solution generated successfully")
            self.logger.info(f"Solution code length: {len(solution_code)} characters")
            
            return solution_code
            
        except Exception as e:
            self.logger.error(f"Groq API call failed: {e}")
            return self._mock_llm_call(problem_data)

    def _clean_code_response(self, code: str) -> str:
        """Clean code response from LLM"""
        # Remove markdown code blocks
        if code.startswith("```python"):
            code = code.replace("```python", "").replace("```", "").strip()
        elif code.startswith("```"):
            code = code.replace("```", "").strip()
        
        # Remove any extra text before/after code
        lines = code.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            if line.strip().startswith('class ') or line.strip().startswith('def '):
                in_code = True
            if in_code:
                code_lines.append(line)
        
        clean_code = '\n'.join(code_lines).strip()
        
        return clean_code

    def _mock_llm_call(self, problem_data: Dict[str, Any]) -> str:
        """Fallback mock solution generator"""
        self.logger.info("Using fallback mock solution generator")
        
        # For the specific problem
        if "paths in matrix whose sum is divisible by k" in problem_data['title'].lower():
            return """class Solution:
    def numberOfPaths(self, grid, k):
        MOD = 10**9 + 7
        m, n = len(grid), len(grid[0])
        dp = [[[0] * k for _ in range(n)] for _ in range(m)]
        dp[0][0][grid[0][0] % k] = 1
        for i in range(m):
            for j in range(n):
                for r in range(k):
                    if dp[i][j][r] > 0:
                        if j + 1 < n:
                            new_r = (r + grid[i][j+1]) % k
                            dp[i][j+1][new_r] = (dp[i][j+1][new_r] + dp[i][j][r]) % MOD
                        if i + 1 < m:
                            new_r = (r + grid[i+1][j]) % k
                            dp[i+1][j][new_r] = (dp[i+1][j][new_r] + dp[i][j][r]) % MOD
        return dp[m-1][n-1][0]"""
        
        # Generic template
        return """class Solution:
    def solve(self, data):
        pass"""

    def input_solution_code(self, solution_code: str) -> bool:
        """Input solution code into the editor"""
        try:
            self.logger.info("Attempting to input solution code...")
            
            # Clear existing code first
            clear_script = """
            // Function to clear editor
            function clearEditor() {
                // Try Monaco editor
                if (window.monaco && window.monaco.editor) {
                    const editors = monaco.editor.getEditors();
                    if (editors.length > 0) {
                        const model = editors[0].getModel();
                        model.setValue('');
                        return true;
                    }
                }
                
                // Try CodeMirror
                const codeMirrors = document.querySelectorAll('.CodeMirror');
                if (codeMirrors.length > 0) {
                    for (let cm of codeMirrors) {
                        if (cm.CodeMirror) {
                            cm.CodeMirror.setValue('');
                            return true;
                        }
                    }
                }
                
                // Try textarea
                const textareas = document.querySelectorAll('textarea');
                for (let textarea of textareas) {
                    if (textarea.offsetHeight > 0) {
                        textarea.value = '';
                        return true;
                    }
                }
                return false;
            }
            clearEditor();
            """
            
            self.driver.execute_script(clear_script)
            time.sleep(1)
            
            # Now input the solution
            input_script = """
            function setCode(solution) {
                // Try Monaco editor
                if (window.monaco && window.monaco.editor) {
                    const editors = monaco.editor.getEditors();
                    if (editors.length > 0) {
                        const model = editors[0].getModel();
                        model.setValue(solution);
                        return true;
                    }
                }
                
                // Try CodeMirror
                const codeMirrors = document.querySelectorAll('.CodeMirror');
                if (codeMirrors.length > 0) {
                    for (let cm of codeMirrors) {
                        if (cm.CodeMirror) {
                            cm.CodeMirror.setValue(solution);
                            return true;
                        }
                    }
                }
                
                // Try textarea
                const textareas = document.querySelectorAll('textarea');
                for (let textarea of textareas) {
                    if (textarea.offsetHeight > 0) {
                        textarea.value = solution;
                        textarea.dispatchEvent(new Event('input', { bubbles: true }));
                        textarea.dispatchEvent(new Event('change', { bubbles: true }));
                        return true;
                    }
                }
                return false;
            }
            return setCode(arguments[0]);
            """
            
            result = self.driver.execute_script(input_script, solution_code)
            
            if result:
                self.logger.info("✅ Solution code input successfully")
                time.sleep(2)
                return True
            else:
                self.logger.warning("JavaScript input failed, trying alternative method...")
                return self._alternative_code_input(solution_code)
                
        except Exception as e:
            self.logger.error(f"Code input failed: {e}")
            return self._alternative_code_input(solution_code)

    def _alternative_code_input(self, solution_code: str) -> bool:
        """Alternative method for code input"""
        try:
            # Click in the editor area
            editor_selectors = [
                "//div[contains(@class, 'CodeMirror')]",
                "//div[contains(@class, 'monaco-editor')]",
                "//div[contains(@class, 'view-lines')]",
                "//textarea"
            ]
            
            for selector in editor_selectors:
                try:
                    editor = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    editor.click()
                    time.sleep(1)
                    break
                except:
                    continue
            
            # Select all and delete
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
            time.sleep(0.5)
            actions.send_keys(Keys.DELETE).perform()
            time.sleep(0.5)
            
            # Type the solution
            actions.send_keys(solution_code).perform()
            time.sleep(2)
            
            self.logger.info("Alternative code input successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Alternative code input failed: {e}")
            return False

    def check_submission_result(self) -> tuple:
        """Check submission result and return (success, result_text)"""
        try:
            # Wait for result to appear
            time.sleep(8)
            
            # Check for various result indicators
            result_selectors = [
                "//div[contains(text(), 'Accepted')]",
                "//span[contains(text(), 'Accepted')]",
                "//div[contains(@data-cy, 'submission-result')]",
                "//div[contains(@class, 'success')]",
                "//div[contains(@class, 'text-success')]",
                "//div[contains(text(), 'Wrong Answer')]",
                "//div[contains(text(), 'Runtime Error')]",
                "//div[contains(text(), 'Time Limit Exceeded')]",
                "//div[contains(text(), 'Compile Error')]"
            ]
            
            for selector in result_selectors:
                try:
                    result_element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    result_text = result_element.text.strip()
                    if result_text:
                        if "Accepted" in result_text:
                            return True, result_text
                        else:
                            return False, result_text
                except:
                    continue
            
            # If no specific result found, check for any result text
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            if "Accepted" in body_text:
                return True, "Accepted (found in body text)"
            elif any(x in body_text for x in ["Wrong Answer", "Runtime Error", "Time Limit Exceeded", "Compile Error"]):
                return False, "Error found in body text"
            
            return False, "Unknown result"
                
        except Exception as e:
            self.logger.error(f"Error checking submission result: {e}")
            return False, f"Error: {str(e)}"

    def submit_solution(self) -> tuple:
        """Submit the solution and return (success, result_text)"""
        try:
            self.logger.info("Looking for submit button...")
            
            # Use the specific submit button selector
            submit_selectors = [
                "//button[@data-e2e-locator='console-submit-button']",
                "//button[contains(@aria-label, 'Submit')]",
                "//button[.//span[contains(text(), 'Submit')]]"
            ]
            
            for selector in submit_selectors:
                try:
                    submit_btn = WebDriverWait(self.driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView();", submit_btn)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", submit_btn)
                    self.logger.info("✅ Submit button clicked successfully")
                    
                    # Check submission result
                    success, result_text = self.check_submission_result()
                    return success, result_text
                    
                except Exception as e:
                    self.logger.warning(f"Submit button not found with selector {selector}: {e}")
                    continue
            
            self.logger.error("❌ Could not find submit button with any selector")
            return False, "Submit button not found"
                
        except Exception as e:
            self.logger.error(f"Submission failed: {e}")
            return False, f"Submission error: {str(e)}"

    def solve_problem_with_feedback(self, problem_url: str) -> bool:
        """Solve problem with feedback loop and retry mechanism"""
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"🚀 Attempt {attempt + 1} for problem")
                
                # Step 1: Extract problem statement
                self.logger.info("Step 1: Extracting problem statement...")
                problem_data = self.extract_problem_statement(problem_url)
                
                if not problem_data:
                    self.logger.error("Failed to extract problem data")
                    continue

                # Step 2: Generate solution using Groq
                self.logger.info("Step 2: Generating solution with Groq...")
                solution_code = self.call_groq_for_solution(problem_data, attempt + 1)
                
                if not solution_code:
                    self.logger.error("Failed to generate solution")
                    continue

                # Step 3: Input solution code
                self.logger.info("Step 3: Inputting solution code...")
                if not self.input_solution_code(solution_code):
                    self.logger.error("Failed to input solution code")
                    continue

                # Step 4: Submit solution and check result
                self.logger.info("Step 4: Submitting solution...")
                success, result_text = self.submit_solution()
                
                if success:
                    self.logger.info(f"🎉 Problem solved successfully on attempt {attempt + 1}!")
                    self.logger.info(f"Result: {result_text}")
                    return True
                else:
                    self.logger.warning(f"❌ Attempt {attempt + 1} failed: {result_text}")
                    
                    # If not last attempt, wait and retry
                    if attempt < self.max_retries - 1:
                        self.logger.info(f"🔄 Retrying in {self.retry_delay} seconds...")
                        time.sleep(self.retry_delay)
                    continue
                    
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed with error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                continue
        
        self.logger.error(f"❌ All {self.max_retries} attempts failed")
        return False

    def run_automation(self, problem_list: list):
        """Run automation for multiple problems"""
        self.logger.info(f"🚀 Starting automation for {len(problem_list)} problems")
        
        solved_count = 0
        for i, problem_url in enumerate(problem_list, 1):
            self.logger.info(f"📝 Processing problem {i}/{len(problem_list)}")
            self.logger.info(f"🔗 URL: {problem_url}")
            
            success = self.solve_problem_with_feedback(problem_url)
            if success:
                solved_count += 1
                self.logger.info(f"✅ Successfully solved problem {i}")
            else:
                self.logger.warning(f"❌ Failed to solve problem {i}")
            
            # Add delay between problems
            if i < len(problem_list):
                self.logger.info("⏳ Waiting before next problem...")
                time.sleep(5)
        
        self.logger.info(f"🏁 Automation completed. Solved {solved_count}/{len(problem_list)} problems")
        print(f"\n🎯 Final Result: Solved {solved_count}/{len(problem_list)} problems")

    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            self.logger.info("🔚 Browser closed")

def main():
    """Main execution function"""
    print("🤖 LeetCode Automation Agent with Groq")
    print("=" * 50)
    
    # Groq API key
    groq_api_key = "Your Key"
    
    agent = LeetCodeAgent(groq_api_key=groq_api_key)
    
    try:
        # Manual login
        if not agent.manual_login():
            print("❌ Manual login failed.")
            return
        
        # Problem URLs
        problem_urls = [
            "https://leetcode.com/problems/two-sum/description/"
        ]
        
        # Start automation
        print(f"\n🚀 Starting automation for {len(problem_urls)} problems...")
        print("🤖 AI will now take over control...")
        agent.run_automation(problem_urls)
        
    except KeyboardInterrupt:
        print("\n⏹️ Automation interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        agent.close()

if __name__ == "__main__":
    main()