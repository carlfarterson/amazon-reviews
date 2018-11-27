'''
Reviews
|------------------------------------------------------------------------------------------------|
|  ASIN  |  date  |  author_id  |  author_name  |  rating  |  title |  description  |  verified  |


Questions
|-----------------------------------------|
|  ASIN  |  date  |  question  |  answer  |


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

	def pull_reviews(prod_code):
		sleep(1 + random.random())
		reviews = driver.find_elements_by_xpath("//div[@id='cm_cr-review_list']/div")

		if len(reviews) == 0:
			invalid_ASINS.append(prod_code)
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
				date = datetime.strptime(data[2], '%B %d, %Y')
				if data[3] == 'Verified Purchase':
					verified = 1
				else:
					verified = 0
				review = ''
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
					driver.find_element_by_xpath("//li[@class='a-last']/a").click()
					return pull_reviews(prod_code)
				except:
					return


	def pull_questions(prod_code):
		sleep(1 + random.random())
		questions = driver.find_elements_by_xpath("//div[@class='a-section askTeaserQuestions']/div")

		if len(questions) == 0:
			return

		for q in questions:
			date = q.find_element_by_xpath("div/div[2]/div[2]/div/div[2]/span[2]").text[2:]
			date = datetime.strptime(date, '%B %d, %Y')
			question = q.find_element_by_xpath("div/div[2]/div/div/div[2]/a/span").text
			answer = q.find_element_by_xpath("div/div[2]/div[2]/div/div[2]/span[1]").text
			questions_df.append([prod_code, date, question, answer])

		try:
			driver.find_element_by_xpath("//li[@class='a-last']/a").click()
			return pull_questions(prod_code)
		except:
			return


	reviews_df = []
	questions_df = []
	invalid_ASINS = []

	driver.get('https://www.amazon.com')

	for x, asin in enumerate(df['ASIN']):
		pbar.update(x + 1)

		# Pull reviews
		reviews_link = 'https://www.amazon.com/product-reviews/' + asin + '/ref=acr_search_see_all?ie=UTF8&showViewpoints=1'
		driver.get(reviews_link)

		pull_reviews(asin)

		if asin in invalid_ASINS:
			continue

		questions_link = 'https://www.amazon.com/ask/questions/asin/'+ asin +'/ref=ask_dp_dpmw_ql_hza?isAnswered=true'
		driver.get(questions_link)

		pull_questions(asin)

	pbar.finish()
	driver.close()
	reviews_df = pd.DataFrame(reviews_df, columns=['ASIN', 'date', 'author_id', 'author_name', 'rating', 'title', 'description', 'verified'])
	questions_df = pd.DataFrame(questions_df, columns=['ASIN', 'date', 'question', 'answer'])

	avg_review = reviews_df.groupby('ASIN')['rating'].mean().tolist()

	num_verified = []
	num_unverified = []
	avg_review_verified = []
	avg_review_unverified = []

	for asin in set(reviews_df['ASIN']):
		temp_verified = reviews_df[(reviews_df['ASIN'] == asin) & (reviews_df['verified'] == 1)]
		num_verified.append(temp_verified.count()['verified'])
		avg_review_verified.append(temp_verified.mean()['rating'])
		temp_unverified = reviews_df[(reviews_df['ASIN'] == asin) & (reviews_df['verified'] == 0)]
		num_unverified.append(temp_unverified.count()['verified'])
		avg_review_unverified.append(temp_unverified.mean()['rating'])


	summary = pd.DataFrame({
		'ASIN': list(set(reviews_df['ASIN'])),
		'reviews_verified': num_verified,
		'reviews_unverified': num_unverified,
		'avg_review': avg_review,
		'avg_review_verified': avg_review_verified,
		'avg_review_unverified': avg_review_unverified
	})

	reviews_df.set_index('ASIN', drop=True, inplace=True)
	questions_df.set_index('ASIN', drop=True, inplace=True)
	summary.set_index('ASIN', drop=True, inplace=True)

	try:
		os.remove('data/reviews.csv')
		os.remove('data/questions.csv')
		os.remove('data/summary.csv')
		os.remove('data/invalid_ASIN.csv')
	except:
		pass

	reviews_df.to_csv('data/reviews.csv')
	questions_df.to_csv('data/questions.csv')
	summary.to_csv('data/summary.csv')

	if len(invalid_ASINS) > 0:
		print('\nUnable to pull data for {} ASINs.  Details available in invalid_ASIN.csv\n'.format(len(invalid_ASINS)))
		pd.DataFrame({'ASIN': invalid_ASINS}).to_csv('data/invalid_ASIN.csv')

if __name__ == '__main__':

	df = pd.read_excel('ASINS_to_scrape.xlsx')

	chrome_options = Options()
	chrome_options.add_argument('--headless')
	chrome_options.add_argument('log-level=3')
	driver = webdriver.Chrome('chromedriver.exe', options=chrome_options)

	widgets = ['ASIN ', SimpleProgress(),'  ', Percentage(), ' ', Bar(marker='#',left='[',right=']'), ' ', ETA()]
	pbar = ProgressBar(widgets=widgets, maxval=len(df)).start()

	main()
	print('Complete!')
