*** Settings ***
Library   Collections
Library   Browser
Library   RequestsLibrary
Library   OperatingSystem
Library   awscli.py
Library   utils.py


Test Setup       Setup context
#Test Teardown    Teardown context

*** Variables ***
${BROWSER}    chrome
${HEADLESS}   False
${data_dir}   %{DATA_DIR}
${img_dir}   ${data_dir}/images
${products_file}   ${data_dir}/data.json
${host_name}   %{HOST_NAME}
${store_id}   %{STORE_ID}
${store_url}   %{STORE_URL}
${product_url}   %{PRODUCT_URL}
${user_agent}   %{USER_AGENT}
${ccc_cookie}   %{CCC_COOKIE}
${ccc_cookie_domain}   %{CCC_COOKIE_DOMAIN}


*** Keywords ***
Setup context
    New Context  userAgent=${user_agent}  locale=uk

    Add Cookie   ccc  ${ccc_cookie}  domain=${ccc_cookie_domain}  path=/
    Set Browser Timeout  30s
    Create Directory  ${data_dir}
    Create Directory  ${img_dir}
#    Create File  ${products_file}

    ${run_id}   Evaluate    uuid.uuid4().hex    modules=uuid
    Set Suite Variable    ${run_id}


JSON Dumps
    [Arguments]    ${data}
    ${result}=    Evaluate    json.dumps(${data}, ensure_ascii=False)    modules=json
    RETURN  ${result}


Scroll Store To Pagination
    Scroll To Element  div[data-qaid="pagination"] >> div[data-qaid="pagination"]


Download Img
    [Arguments]    ${url}
    ${response}    GET  ${url}
    ${file_name}  Evaluate  "${url}".split("/")[-1]
    ${file_name}  Evaluate  "${file_name}".split("?")[0]
    Create Binary File   ${img_dir}/${file_name}   ${response.content}
    RETURN  ${file_name}


#Click Robot Checkbox
#
#    ${iframes}  Get Elements  iframe[title="reCAPTCHA"]
#    FOR  ${iframe}  IN   @{iframes}
#        Focus  ${iframe}
#        Sleep  1s
#        Take Screenshot
#        ${checkboxes}  Get Elements  ${iframe} >> span[role="checkbox"]
#        FOR  ${checkbox}  IN   @{checkboxes}
#            Click  ${checkbox}
#        END
#    END


Get Product
    [Arguments]    ${url}
    New Page   ${url}
    Sleep  3s

    ${uuid}  Evaluate  "${url}".split("/")[-1].split(".")[0]
    ${name}  Get Text  h1[data-qaid="product_name"]
    ${sku}   Get Text  span[data-qaid="product-sku"]

    ${presence_found}  Get Element Count    span[data-qaid="product_presence"]
    IF  ${presence_found} > 0
        ${presence}   Get Text  span[data-qaid="product_presence"]
    ELSE
        ${presence}  Set Variable   Недоступний
    END


    ${price}  Get Attribute  div[data-qaid="main_product_info"] >> div[data-qaid="product_price"]  data-qaprice
    ${currency}  Get Attribute  div[data-qaid="main_product_info"] >> div[data-qaid="product_price"]  data-qacurrency
    ${description_html}  Get Property  div[data-qaid="descriptions"]   innerHTML
    ${matches}  Find Images In Text   ${description_html}
    FOR  ${match}  IN  @{matches}
        ${file_name}  Download Img    ${match}
        ${description_html}  Replace Image In Text  ${description_html}   ${match}   ${file_name}
    END

    ${categories}  Create List
    ${cat_elements}  Get Elements  li[data-qaid="breadcrumbs_seo_item"]
    FOR    ${el}    IN    @{cat_elements}
        ${text}  Get Text  ${el}
        Append To List  ${categories}  ${text}
    END


    ${more_attr_count}  Get Element Count    button[data-qaid="all_attributes"]
    IF  ${more_attr_count} > 0
        Click  button[data-qaid="all_attributes"]
    END
    &{attrs}  Create Dictionary
    ${attributes}  Get Elements  li[data-qaid="attributes"] >> ul>li>div>div:last-child
    FOR    ${attr}    IN    @{attributes}
        ${at_name}  Get Attribute  ${attr}  data-qaid
        ${at_value}  Get Text  ${attr}
        Set To Dictionary  ${attrs}  ${at_name}  ${at_value}
    END

    Click  div[data-qaid="image_block"]
    Sleep  1s
    ${img_items}  Get Elements  img[data-qaid="photo_gallery_main_image"]
    ${img_names}  Create List
    FOR    ${img}    IN    @{img_items}
        ${img_src}  Get Attribute  ${img}  src
        ${file_name}  Download Img  ${img_src}
        Append To List  ${img_names}  ${file_name}
    END

    Close Page

    &{result}  Create Dictionary  id=${uuid}  name=${name}  sku=${sku}  presence=${presence}  price=${price}  currency=${currency}  attributes=${attrs}  description=${description_html}  images=${img_names}  categories=${categories}
    ${json_str}  JSON Dumps    ${result}
    RETURN  ${json_str}


Sync Data
    [Arguments]    ${store_id}
    Sync Media Files To S3   dir_name=${img_dir}   store_id=${store_id}
    Sync Data Files To S3    data_file=${products_file}   store_id=${store_id}


*** Test Cases ***
Get Store
    [Documentation]  Get Data
    [Tags]    store
    New Page  ${store_url}
    ${size}  Get Viewport Size  ALL

    ${current_url}  Set Variable   ${store_url}
    WHILE  ${True}  # wait for BREAK
        # scroll  to load all elements on screen
        Scroll To Element  div[data-qaid="product_gallery"]
        Sleep  2s
        Scroll Store To Pagination

        # get all products from this page
        ${prod_links}  Get Elements  a[data-qaid="product_link"]
        FOR    ${el}    IN    @{prod_links}
            ${link}  Get Property  ${el}  href

            ${product_json}  Get Product  url=${link}
            Append To File  ${products_file}  ${product_json}\n
        END

        ${next_page_count}  Get Element Count    a[data-qaid="next_page"]
        IF  ${next_page_count} > 0
            Click  a[data-qaid="next_page"]
        ELSE
            BREAK  # breaks WHILE
        END
    END

    Sync Data   store_id=${store_id}


Get Product
    [Documentation]  Get Data
    [Tags]    product
    ${product_json}  Get Product  url=${product_url}
    Log  ${product_json}


Sync Data Test
    [Documentation]  Sync Data
    [Tags]    sync
    Sync Data   store_id=${store_id}