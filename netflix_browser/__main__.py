
import sys
import netflix_browser


def main(argv=sys.argv):
    app = netflix_browser.Application()
    app.run(argv)


if __name__ == '__main__':
    main()
