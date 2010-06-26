import web

db = web.database(dbn='postgres', host="localhost", user='yt', pw='pwd123', db='ytmndstream')

urls = (
  '/', 'index'
)

class index:
    def GET(self):
        videos = db.select('videos')
        result = ""
        for video in videos:
          result = str(video.id) + " " + result
        return result 

app = web.application(urls, globals())

if __name__ == "__main__": app.run()

