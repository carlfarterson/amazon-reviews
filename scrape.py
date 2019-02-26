'''
Reviews
|------------------------------------------------------------------------------------------------|
|  ASIN  |  date  |  author_id  |  author_name  |  rating  |  title |  description  |  verified  |


Questions
|--------------------------------------------------------------|
|  ASIN  |  date  |  question  |  answer  |  author_of_answer  |


Summary
|---------------------------------------------------------------------------------------------------------------------|
|  ASIN  |  reviews_verified  |  reviews_unverified  |  avg_review  |  avg_review_verified  |  avg_review_unverified  |

'''
import os
import random
import pandas as pd
from datetime import datetime
from time import sleep
from driver import Chrome
from progressbar import ProgressBar, Percentage, Bar, ETA, SimpleProgress

# Progress bar to show current status of web scrape
widgets = ['ASIN ', SimpleProgress(),'  ', Percentage(), ' ', Bar(marker='#',left='[',right=']'), ' ', ETA()]
pbar = ProgressBar(widgets=widgets, maxval=len(df)).start()

chrome = Chrome()


# bot start time
t0 = datetime.now()

# Dataframes to store scrape information
reviews_df = pd.DataFrame(columns=['ASIN', 'date', 'author_id', 'author_name', 'rating', 'title', 'description', 'verified'])
questions_df = pd.DataFrame(columns=['ASIN', 'date', 'question', 'answer', 'author_of_answer'])
invalid_ASINs = []

asins = pd.read_excel('ASINs_to_scrape.xlsx')['ASIN'].tolist()
for i, asin in enumerate(asins):

	# Refresh chrome every 10 ASIN's scraped
	if i % 10 == 0:
		chrome = Chrome()

	pbar.update(x + 1)

	# Pull reviews
	reviews_url = 'https://www.amazon.com/product-reviews/' + asin + '/ref=acr_search_see_all?ie=UTF8&showViewpoints=1'
	chrome.goto(reviews_url)

	while True:
		reviews = chrome.xpath('//div[@data-hook="review"]', isList=True)
		# Append ASIN to invalid_ASINs if there are no reviews for the item
		if len(reviews) == 0:
			invalid_ASINs = invalid_ASINs.append(asin)
			break

		for review in reviews:

			review_id = review.get_attribute('id')

			rating = review.find_element_by_xpath('div/div/div[2]/a').get_attribute('title')
			rating = float(rating[:rating.find(' ')])

			author_id = el.find_element_by_xpath('div/div/div/a').get_attribute('href')
			author_id = author_id[author_id.find('account.') + len('account.'):author_id.find('/ref')]

			results = el.text.split('\n')
			author_name = results[0]

			if 'TOP' in results[1]:
				results.pop(1)

			title = results[1]
			try:
				date = datetime.strptime(results[2], '%B %d, %Y')
			except:
				date = None

			description = ''
			num_helped = 0
			verified = False
			for val in results[3:]:
				if 'Helpful' in val:
					break
				elif 'Verified Purchase' in val:
					verified = True
				elif 'found this helpful' in val:
					if 'One person' in val:
						num_helped = 1
					else:
						num_helped = int(val[:val.find(' ')])
					break
				else:
					description += val

			reviews_df.append({
				'ASIN': asin,
				'date': date,
				'author_id': author_id,
				'author_name': author_name,
				'rating': rating,
				'title': title,
				'description': description,
				'verified': verified
			}, ignore_index=True)

		# Click to next page of reviews
		try:
			chrome.xpath("//li[@class='a-last']/a").click()
		except:
			break

	# Pull questions
	questions_link = 'https://www.amazon.com/ask/questions/asin/'+ asin +'/ref=ask_dp_dpmw_ql_hza?isAnswered=true'
	chrome.goto(questions_link)
	while True:
		questions = chrome.xpath("//div[@class='a-section askTeaserQuestions']/div", isList=True)
		# Exit if there are no questions for the ASIN
		if len(questions) == 0:
			break

		for q in questions:
			date = chrome.get_text(container=q, path="div/div[2]/div[2]/div/div[2]/span[2]")[2:]
			try:
				date = datetime.strptime(date, '%B %d, %Y')
			except:
				date = ''

			question = chrome.get_text(container=q, path=)
			question = q.find_element_by_xpath("div/div[2]/div/div/div[2]/a/span").text
			
			answer = q.find_element_by_xpath("div/div[2]/div[2]/div/div[2]/span[1]").text
			chrome.get_text(container=q, path= "div/div[2]/div[2]/div/div[2]/span[1]")
			author_of_answer = q.find_element_by_xpath("//div[@class='a-profile-content']/span[@class='a-profile-name']").text
			questions_df.append([asin, date, question, answer, author_of_answer])

		try:
			# Click to the next page of questions
			chrome.xpath("//li[@class='a-last']/a").click()
		except:
			break

# Close progress bar and chrome instance
pbar.finish()
driver.close()

# Delete any files if they exist before creating our new files
files = ['reviews.csv', 'questions.csv', 'summary.csv', 'invalid_ASINs.csv', 'web scrape summary.txt']
for file in files:
	try:
		os.remove('data/' + file)
	except:
		continue

# Saving our reviews and questions to CSV
reviews_df.to_csv('data/reviews.csv', index=False)
questions_df.to_csv('data/questions.csv', index=False)

# Columns to be used for the summary
num_verified = []
num_unverified = []
avg_review_verified = []
avg_review_unverified = []

reviews_df = pd.read_csv('data/reviews.csv')

asins = list(set(reviews_df['ASIN']))
avg_review = reviews_df.groupby('ASIN')['rating'].mean().tolist()

for asin in asins:
	temp_verified = reviews_df[(reviews_df['ASIN'] == asin) & (reviews_df['verified'] == 1)]
	num_verified.append(temp_verified.count()['verified'])
	avg_review_verified.append(temp_verified.mean()['rating'])
	temp_unverified = reviews_df[(reviews_df['ASIN'] == asin) & (reviews_df['verified'] == 0)]
	num_unverified.append(temp_unverified.count()['verified'])
	avg_review_unverified.append(temp_unverified.mean()['rating'])

# Saving our summary to CSV
summary_df = pd.DataFrame({
	'ASIN': list(set(reviews_df['ASIN'])),
	'reviews_verified': num_verified,
	'reviews_unverified': num_unverified,
	'avg_review': avg_review,
	'avg_review_verified': avg_review_verified,
	'avg_review_unverified': avg_review_unverified
})
summary_df.to_csv('data/summary.csv', index=False)

# Make invalid_ASINs CSV if there were invalid ASINS in the dataset
if len(invalid_ASINs) > 0:
	print('\nUnable to pull data for {} ASINs.  Details available in invalid_ASINs.csv\n'.format(len(invalid_ASINs)))
	temp = pd.DataFrame({'ASIN': invalid_ASINs})
	temp.to_csv('data/invalid_ASIN.csv')

# bot finish time
t1 = datetime.now()

# Total time to run (timedelta object)
delta = t1 - t0

num_asins = len(summary_df)
num_reviews = len(reviews_df)
num_questions = len(questions_df)

with open('data/web scrape summary.txt', 'w') as file:
	file.write('Time to run            :  {} minutes\n'.format(round(delta.seconds/60, 2)))
	file.write('# of ASINS pulled      :  {}\n'.format(num_asins))
	file.write('Average time per ASIN  :  {} seconds\n'.format(round(delta.seconds/num_asins, 2)))
	file.write('# of reviews           :  {}\n'.format(num_reviews))
	file.write('# of questions         :  {}\n'.format(num_questions))

print('Complete!')
sleep(10)
