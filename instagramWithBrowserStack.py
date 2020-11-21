from appium import webdriver
from appium.webdriver.common.mobileby import MobileBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import subprocess
import json
import sys

userName = sys.argv[3]
accessKey = sys.argv[4]
appID = sys.argv[5]

filePath = sys.argv[6]
postVideo = subprocess.check_output(['curl', '-s', '-u', userName+':'+accessKey, '-X', 'POST', 'https://api-cloud.browserstack.com/app-automate/upload-media', '-F', 'file=@'+filePath])
mediaLink = postVideo.decode('utf-8')
res = json.loads(mediaLink)
mediaLink = res["media_url"]

desired_caps = {
    "build": "Python Android",
    "device": "Google Pixel 3",
    "app": appID,
    'browserstack.appium_version': '1.9.1',
    "browserstack.uploadMedia": [mediaLink]
}

username = sys.argv[1]
password = sys.argv[2]
caption = sys.argv[7]

driver = webdriver.Remote("https://" + userName + ":" + accessKey + "@hub-cloud.browserstack.com/wd/hub", desired_caps)

time.sleep(5)

logInButton = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((MobileBy.ID, "com.instagram.android:id/log_in_button"))
)
logInButton.click()
time.sleep(2)

userID = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((MobileBy.ID, "com.instagram.android:id/login_username"))
)
userID.send_keys(username)

passwordBox = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((MobileBy.ID, "com.instagram.android:id/password"))
)
passwordBox.send_keys(password)
time.sleep(2)

logIn = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((MobileBy.ID, "com.instagram.android:id/button_text"))
)
logIn.click()
time.sleep(5)

uploadMedia = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((MobileBy.XPATH, "//android.widget.Button[@content-desc='Camera']"))
)
uploadMedia.click()
time.sleep(3)

storagePermission = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((MobileBy.XPATH, "//android.widget.Button[@text='Allow']"))
)
storagePermission.click()
time.sleep(5)

chooseFile = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((MobileBy.XPATH, "//android.widget.CheckBox[@index='0']"))
)
chooseFile.click()
time.sleep(5)

cropToggle = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((MobileBy.ACCESSIBILITY_ID, "Toggle square"))
)
cropToggle.click()
time.sleep(3)

selectMedia = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((MobileBy.ACCESSIBILITY_ID, "Next"))
)
selectMedia.click()
time.sleep(3)

nextStep = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((MobileBy.ACCESSIBILITY_ID, "Next"))
)
nextStep.click()
time.sleep(2)

captionBox = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((MobileBy.ID, "com.instagram.android:id/caption_text_view"))
)
captionBox.send_keys(caption)
time.sleep(5)

share = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((MobileBy.ACCESSIBILITY_ID, "Next"))
)
share.click()
time.sleep(60)

goToProfile = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((MobileBy.ID, "com.instagram.android:id/profile_tab"))
)
goToProfile.click()
time.sleep(3)

selectRecentPost = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((MobileBy.XPATH, "//androidx.recyclerview.widget.RecyclerView/android.widget.LinearLayout[@index='1']/android.widget.ImageView[@index='0']"))
)
selectRecentPost.click()
time.sleep(3)

moreFeedOptions = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((MobileBy.ID, "com.instagram.android:id/feed_more_button_stub"))
)
moreFeedOptions.click()
time.sleep(3)

copyLink = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((MobileBy.XPATH, "//android.widget.TextView[@text='Copy Link']"))
)
copyLink.click()
time.sleep(15)

postLink = driver.get_clipboard_text()
print("Instagram Link: " + postLink)

mediaHash = mediaLink.replace("media://","")
subprocess.call(['curl', '-s', '-u', userName+':'+accessKey, '-X', 'DELETE', 'https://api-cloud.browserstack.com/app-automate/custom_media/delete/'+mediaHash])

driver.quit()