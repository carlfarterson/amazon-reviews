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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd
from progressbar import ProgressBar, Percentage, Bar, ETA, SimpleProgress
import os
from datetime import datetime
from time import sleep
import random


def main():


	def pull_reviews(prod_code, num_clicks):

		# Wait a few seconds for page to load before pulling elements from page
		sleep(2 + random.random()/3)
		reviews = driver.find_elements_by_xpath("//div[@id='cm_cr-review_list']/div")

		# Append ASIN to invalid_ASINs if there are no reviews for the item
		if len(reviews) == 0:
			invalid_ASINs.append(prod_code)
			return

		for el in reviews:
			try:
				review_id = el.get_attribute('id')
				temp = el.find_elements_by_xpath('div/div')
				rating = temp[1]
				rating = rating.find_element_by_xpath('a[1]').get_attribute('title')
				rating = float(rating[:rating.find(' ')])
				author_id = temp[0]
				author_id = author_id.find_element_by_xpath('a').get_attribute('href')
				author_id = author_id[author_id.find('account.') + len('account.'):author_id.find('/ref')]

				data = el.text.split('\n')
				author_name = data[0]
				title = data[1]

				try:
					date = datetime.strptime(data[2], '%B %d, %Y')
				except:
					date = ''

				if data[3] == 'Verified Purchase':
					verified = 1
				else:
					verified = 0

				review = ''

				# Number of people helped by this review
				for i in range(4,len(data)):
					if data[i].find('Helpful') != -1 or data[i].find(' found this helpful') != -1:
						if data[i].find(' found this helpful') == -1:
							num_helped = 0
						else:
							if data[i].find('One person') != -1:
								num_helped = 1
							else:
								num_helped = int(data[i][:data[i].find(' ')])

						break

					review = review + '  ' + data[i]

				reviews_df.append([prod_code, date, author_id, author_name, rating, title, review, verified])

			except:
				try:
					# Click to next page of reviews
					driver.find_element_by_xpath("//li[@class='a-last']/a").click()
					num_clicks += 1
					return pull_reviews(prod_code, num_clicks)
				except:
					return


	def pull_questions(prod_code, num_clicks):

		# Wait a few seconds for page to load before pulling elements from page
		sleep(2 + random.random()/2)
		questions = driver.find_elements_by_xpath("//div[@class='a-section askTeaserQuestions']/div")

		# Exit if there are no questions for the ASIN
		if len(questions) == 0:
			return

		for q in questions:

			date = q.find_element_by_xpath("div/div[2]/div[2]/div/div[2]/span[2]").text[2:]
			try:
				date = datetime.strptime(date, '%B %d, %Y')
			except:
				date = ''

			question = q.find_element_by_xpath("div/div[2]/div/div/div[2]/a/span").text
			answer = q.find_element_by_xpath("div/div[2]/div[2]/div/div[2]/span[1]").text
			author_of_answer = q.find_element_by_xpath("//div[@class='a-profile-content']/span[@class='a-profile-name']").text
			questions_df.append([prod_code, date, question, answer, author_of_answer])

		try:
			# Click to the next page of questions
			driver.find_element_by_xpath("//li[@class='a-last']/a").click()
			num_clicks += 1
			return pull_questions(prod_code, num_clicks)
		except:
			return



	# Add options to make chrome headless and run in background
	chrome_options = Options()
	chrome_options.add_argument('--headless')
	chrome_options.add_argument('log-level=3')
	chrome_options.add_argument('--disable-extensions')
	chrome_options.add_argument('test-type')

	driver = webdriver.Chrome('chromedriver.exe', options=chrome_options)

	# Dataframes to store scrape information
	reviews_df = []
	questions_df = []
	invalid_ASINs = []

	# initialize basic web page
	driver.get('https://www.google.com')
	sleep(3)

	# Loop through all ASINS to pull their reviews and questions
	num_clicks = 0
	for x, asin in enumerate(df['ASIN']):

		# reset the web scraper every 10 ASINS since it slows down after a while
		if num_clicks > 30:
			num_clicks = 0
			driver.close()
			sleep(2)
			driver = webdriver.Chrome('chromedriver.exe', options=chrome_options)
			driver.get('https://www.google.com')
			sleep(3)

		pbar.update(x + 1)

		# Pull reviews
		reviews_link = 'https://www.amazon.com/product-reviews/' + asin + '/ref=acr_search_see_all?ie=UTF8&showViewpoints=1'
		driver.get(reviews_link)
		pull_reviews(asin, num_clicks)

		# go to the next ASIN if there were no reviews for the item
		if asin in invalid_ASINs:
			continue

		# Pull questions
		questions_link = 'https://www.amazon.com/ask/questions/asin/'+ asin +'/ref=ask_dp_dpmw_ql_hza?isAnswered=true'
		driver.get(questions_link)
		pull_questions(asin, num_clicks)

	# Close progress bar and chrome instance
	pbar.finish()
	driver.close()

	# Delete any files if they exist before creating our new files
	files = ['reviews.csv', 'questions.csv', 'summary.csv', 'invalid_ASINs.csv', 'web scrape summary.txt']
	for file in files:
		try:
			os.remove('data/' + file)
		except:
			pass

	# Saving our reviews and questions to CSV
	reviews_df = pd.DataFrame(reviews_df, columns=['ASIN', 'date', 'author_id', 'author_name', 'rating', 'title', 'description', 'verified'])
	questions_df = pd.DataFrame(questions_df, columns=['ASIN', 'date', 'question', 'answer', 'author_of_answer'])

	reviews_df.set_index('ASIN', drop=True, inplace=True)
	questions_df.set_index('ASIN', drop=True, inplace=True)

	reviews_df.to_csv('data/reviews.csv')
	questions_df.to_csv('data/questions.csv')

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
	summary = pd.DataFrame({
		'ASIN': list(set(reviews_df['ASIN'])),
		'reviews_verified': num_verified,
		'reviews_unverified': num_unverified,
		'avg_review': avg_review,
		'avg_review_verified': avg_review_verified,
		'avg_review_unverified': avg_review_unverified
	})

	summary.set_index('ASIN', drop=True, inplace=True)

	summary.to_csv('data/summary.csv')

	# Make invalid_ASINs CSV if there were invalid ASINS in the dataset
	if len(invalid_ASINs) > 0:
		print('\nUnable to pull data for {} ASINs.  Details available in invalid_ASINs.csv\n'.format(len(invalid_ASINs)))
		temp = pd.DataFrame({'ASIN': invalid_ASINs})
		temp.to_csv('data/invalid_ASIN.csv')



if __name__ == '__main__':

	# bot start time
	t0 = datetime.now()

	df = pd.read_excel('ASINs_to_scrape.xlsx')
	asin = df['ASIN'][0]



	# Progress bar to show current status of web scrape
	widgets = ['ASIN ', SimpleProgress(),'  ', Percentage(), ' ', Bar(marker='#',left='[',right=']'), ' ', ETA()]
	pbar = ProgressBar(widgets=widgets, maxval=len(df)).start()

	main()

	num_asins = len(pd.read_csv('data/summary.csv'))
	num_reviews = len(pd.read_csv('data/reviews.csv'))
	num_questions = len(pd.read_csv('data/questions.csv'))

	# bot finish time
	t1 = datetime.now()

	# Total time to run (timedelta object)
	delta = t1 - t0

	with open('data/web scrape summary.txt', 'w') as file:
		file.write('Time to run            :  {} minutes\n'.format(round(delta.seconds/60, 2)))
		file.write('# of ASINS pulled      :  {}\n'.format(num_asins))
		file.write('Average time per ASIN  :  {} seconds\n'.format(round(delta.seconds/num_asins, 2)))
		file.write('# of reviews           :  {}\n'.format(num_reviews))
		file.write('# of questions         :  {}\n'.format(num_questions))

	print('Complete!')
	sleep(10)
