import os
import random
import pandas as pd
from datetime import datetime
from time import sleep
from driver import Chrome
from progressbar import ProgressBar, Percentage, Bar, ETA, SimpleProgress

# Dataframes to store scrape information
reviews_df = pd.DataFrame(columns=['ASIN', 'date', 'author_id', 'author_name', 'rating', 'title', 'description', 'verified'])
questions_df = pd.DataFrame(columns=['ASIN', 'date', 'question', 'answer', 'author_of_answer'])
summary_df = pd.DataFrame(columns=['ASIN', 'avg_rating', 'avg_rating_verified', 'avg_rating_unverified'])
invalid_ASINs = pd.DataFrame(columns=['ASIN'])

asins = pd.read_excel('ASINs_to_scrape.xlsx')['ASIN'].tolist()

# Progress bar to show current status of web scrape
widgets = ['ASIN ', SimpleProgress(),'  ', Percentage(), ' ', Bar(marker='#',left='[',right=']'), ' ', ETA()]
pbar = ProgressBar(widgets=widgets, maxval=len(asins)-1).start()

# bot start time
t0 = datetime.now()

for i, asin in enumerate(asins):

	# Refresh chrome every 10 ASIN's scraped
	if i % 10 == 0:
		chrome = Chrome()

	pbar.update(i)

	# Pull reviews
	reviews_url = 'https://www.amazon.com/product-reviews/' + asin + '/ref=acr_search_see_all?ie=UTF8&showViewpoints=1'
	chrome.driver.get(reviews_url)

	while True:
		sleep(1.75 + random.random() / 4)
		reviews = chrome.driver.find_elements_by_xpath('//div[@data-hook="review"]')
		# Append ASIN to invalid_ASINs if there are no reviews for the item
		if len(reviews) == 0:
			invalid_ASINs = invalid_ASINs.append({'ASIN': asin}, ignore_index=True)
			break

		for review in reviews:

			review_id = review.get_attribute('id')

			rating = review.find_element_by_xpath('div/div/div[2]/a').get_attribute('title')
			rating = float(rating[:rating.find(' ')])

			author_id = review.find_element_by_xpath('div/div/div/a').get_attribute('href')
			author_id = author_id[author_id.find('account.') + len('account.'):author_id.find('/ref')]

			results = review.text.split('\n')
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

			reviews_df = reviews_df.append({'ASIN': asin,
							   'date': date,
							   'author_id': author_id,
							   'author_name': author_name,
							   'rating': rating,
							   'title': title,
							   'description': description,
							   'verified': verified}, ignore_index=True)

		try:
			chrome.driver.find_element_by_xpath("//li[@class='a-last']/a").click()
		except:
			break

	# Pull questions
	questions_link = 'https://www.amazon.com/ask/questions/asin/'+ asin +'/ref=ask_dp_dpmw_ql_hza?isAnswered=true'
	chrome.driver.get(questions_link)

	while True:
		sleep(2.0 + random.random()/3)
		questions = chrome.driver.find_elements_by_xpath("//div[@class='a-section askTeaserQuestions']/div")
		# Exit if there are no questions for the ASIN
		if len(questions) == 0:
			break

		for question in questions:
			results = question.text.split('\n')
			for index, value in enumerate(results):
				if 'Question' in value:
					question_asked = results[index + 1]
				elif 'Answer' in value:
					answer = results[index + 1]
				elif ' · ' in value:
					author, date = value.split(' · ')
					try:
						date = datetime.strptime(date, '%B %d, %Y')
					except:
						date = None

			questions_df = questions_df.append({'asin': asin,
								 'date': date,
								 'question_asked': question_asked,
								 'answer': answer,
								 'author_of_answer': author}, ignore_index=True)

		try:
			chrome.driver.find_element_by_xpath("//li[@class='a-last']/a").click()
		except:
			break

	# Add to summary
	df = reviews_df[reviews_df['ASIN'] == asin]
	avg_rating = df['rating'].mean()

	verified_df = df[df['verified'] == True]
	avg_rating_verified = verified_df['rating'].mean()
	num_ratings_verified = len(verified_df)

	unverified_df = df[df['verified'] == False]
	avg_rating_unverified = unverified_df['rating'].mean()
	num_ratings_unverified = len(unverified_df)
	summary_df = pd.DataFrame(columns=['ASIN', 'avg_rating', 'avg_rating_verified', 'avg_rating_unverified'])

	summary_df = summary_df.append({'ASIN': asin,
								    'avg_rating': avg_rating,
									'avg_rating_verified': avg_rating_verified,
									'avg_rating_unverified': avg_rating_unverified,
								    'num_ratings_verified': num_ratings_verified,
								    'num_ratings_unverified': num_ratings_unverified}, ignore_index=True)


# Close progress bar and chrome instance
pbar.finish()
chrome.driver.close()

# Delete any files if they exist before creating our new files
files = ['reviews.csv', 'questions.csv', 'summary.csv', 'invalid_ASINs.csv', 'web scrape summary.txt']
for file in files:
	try:
		os.remove('data/' + file)
	except:
		continue

# Saving results to CSV
summary_df.to_csv('data/summary.csv', index=False)
reviews_df.to_csv('data/reviews.csv', index=False)
questions_df.to_csv('data/questions.csv', index=False)
if len(invalid_ASINs) > 0:
	pd.DataFrame({'ASIN': invalid_ASINs}).to_csv('data/invalid_ASINs.csv')

# bot finish time
t1 = datetime.now()

# Total time to run
delta = t1 - t0

with open('data/web scrape summary.txt', 'w') as file:
	file.write('Time to run            	 :  {} minutes\n'.format(round(delta.seconds/60, 2)))
	file.write('\n# of ASINs pulled		 :  {}'.format(len(asins)))
	file.write('\n# of invalid ASINs     :  {} '.format(len(invalid_ASINs)))
	file.write('\nAverage time per ASIN  :  {} seconds\n'.format(round(delta.seconds/len(asins), 2)))
	file.write('\n# of reviews           :  {}'.format(len(reviews_df)))
	file.write('\n# of questions         :  {}'.format(len(questions_df)))
