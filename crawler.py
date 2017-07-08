import argparse

parse = argparse.ArgumentParser(description='YoupinCrawler')
parse.add_argument('-s', '-spider',
                   nargs=1, dest='spider',
                   metavar='<s>', required=True,
                   help='爬虫名称，linkedin, maimai,...')
parse.add_argument('-a', '-action',
                   nargs=1, dest='action',
                   metavar='<a>', required=True,
                   help='爬虫行为, check, dist1, detail, contact,..')
parse.add_argument('-n', dest='n', type=int,
                   metavar='<n>', required=False,
                   help='第<n>次爬取或用户状态值')
args = parse.parse_args()
# print(args)

if 'maimai' in args.spider:
    from maimai import spider
elif 'linkedin' in args.spider:
    from linkedin import spider

if 'check' in args.action:
    spider.check_account(args.n)
elif 'dist1' in args.action:
    spider.crawl_dist1(args.n)
elif 'detail' in args.action:
    spider.crawl_detail()
elif 'contact' in args.action:
    spider.crawl_contact()
