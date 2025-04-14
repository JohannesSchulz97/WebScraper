
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
