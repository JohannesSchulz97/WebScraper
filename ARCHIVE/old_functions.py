
async def is_inside_figure(element, root):
    parent = await element.evaluate_handle('(el) => el.parentElement')
    while parent:
        if parent == root:
            return False
        data_testid = await parent.get_attribute("data-testid")
        class_name = await element.get_attribute("class") or ""
        if "Figure" in class_name or data_testid == "baseillustrative":
            return True
        # Move one level up
        new_parent = await parent.evaluate_handle('(el) => el.parentElement')
        if await new_parent.evaluate('(el) => el === null'):
            break
        parent = new_parent
    return False
            

"""
    Finds all collapsed sections and expands them by clicking.
    Only clicks buttons with class names containing 'SectionDataComponent' or 'AccordionSectionComponent'.
"""
async def expand_all_sections(page, max_rounds=10, headless=False):
    expanded_count = 0

    for round_num in range(max_rounds):
        print(f"\n🔁 Expansion round {round_num + 1}")
        buttons = await page.query_selector_all('button[aria-expanded="false"]')
        clicked_this_round = 0
        for i, button in enumerate(buttons):
    
            try:
                class_name = await button.get_attribute("class") or ""
                if "SectionDataComponent" not in class_name and "AccordionSectionComponent" not in class_name:
                    continue

                # Scroll into view and click
                await button.scroll_into_view_if_needed()
                if headless: 
                    await button.click()
                else:
                    await page.wait_for_timeout(100)
                    await button.click()
                    await page.wait_for_timeout(100)

                expanded_count += 1
                clicked_this_round += 1

            except Exception as e:
                print(f"⚠️ Could not click button #{i}: {e}")
                continue
            if expanded_count > 10:
                await page.wait_for_timeout(1000)
                return

        if clicked_this_round == 0:
            print("✅ No more buttons to expand.")
            break

    print(f"\n✅ Finished. Expanded {expanded_count} sections total.")



"""
async def extract_introduction(element):
    children = await element.query_selector_all(':scope > *')
    content = ""
    
    for child in children:
        tag = await child.evaluate('(el) => el.tagName')

        if tag == "SECTION":
            return content.strip()  # Stop at the first section

        elif tag == "P":
            if not await child.get_attribute("data-testid") == "topicPara":
                continue
            text = await child.inner_text()
            text = text.strip()
            if text:
                content += text + "\n"

        elif tag == "DIV":
            data_testid = await element.get_attribute("data-testid")
            class_name = await element.get_attribute("class") or ""
            if "Figure" in class_name or data_testid == "baseillustrative":
                continue
            content += await extract_introduction(child)
    return content.strip()

async def get_element_depth(elem, root):
    return await elem.evaluate(
        "(el, root) => { let d = 0; while (el && el !== root) { d++; el = el.parentElement; } return d; }",
        root
    )


async def parse_element(element, title=None):
    content_dict = {}

    # Optional: Store section title
    if not title: 
        first_heading = await element.query_selector('h1, h2, h3, h4, h5, h6')
        title = (await first_heading.inner_text()).strip() if first_heading else "Untitled"
    content_dict["title"] = title

    # Fix: Await this!
    content_dict["content"] = await extract_introduction(element)

    # Parse subsections recursively
    sections = await element.query_selector_all('section')    
    if not sections:
        return content_dict
    reference_depth = await get_element_depth(sections[0], element)

    for section in sections:
        depth = await get_element_depth(section, element)
        if depth != reference_depth:
            continue
        section_content = await parse_element(section)
        section_title = section_content.get("title", "Untitled Section")
        content_dict[section_title] = section_content

    return content_dict
"""

"""
    Tries to accept the cookie banner if it exists on the page.
    Prevents interference with future button clicks.
"""
async def accept_cookies(page):
    try:
        await page.click("#onetrust-accept-btn-handler", timeout=5000)
        print("Accepted cookies.")
        await page.wait_for_timeout(1000)
    except Exception as e:
        print("No cookie banner found or could not click it:", e)

