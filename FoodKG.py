'''
This is the main file. It will run Flask server and load the models ...
'''

from flask import Flask, render_template, request, after_this_request, make_response, send_file, redirect
import werkzeug
import os
import shutil
from prepare_Models import prepare_Models

app = Flask(__name__)

dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)

context = ''
relationToUse = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
mainSim, hashOut = 0, 0
subToUse, objToUse = '', ''


# Create a temp file to be used to store the triples between every write
def createTemp(filename):
    with open(filename) as reader:
        with open('temp.nt', 'w+') as writer:
            for line in reader:
                writer.write(line)

# a method to handle user get & post responses and delete the actual triples after the overwrite
@app.route('/database', methods=['GET', 'POST'])
def upload_file():
    global context
    from addContext import readFile as contextReadFile
    if request.method == 'POST':
        contexT = request.form['context']
        context = contexT
        f = request.files['file']
        f.save(werkzeug.secure_filename(f.filename))
        # Finaldata = readFile(f.filename)
        Finaldata = contextReadFile(f.filename, contexT)
        createTemp(f.filename)
        filename = Finaldata

        @after_this_request
        def remove_file(response):
            try:
                os.remove(f.filename)
                # readDate.readerIn.close()
            except Exception as error:
                app.logger.error("Error removing or closing downloaded file handle", error)
            return response

        def download(response):
            response = make_response(Finaldata)
            response.headers["Content-Disposition"] = "attachment; filename=result.txt"
            render_template('upload.html', filename=filename)
            return response

        return render_template('upload.html', filename=filename)



# Routing function for the entity extraction script
@app.route('/extractEntity')
def extractEntity():
    from entityEtra import readFile as entityReadFile
    filename = entityReadFile('temp.nt', context)
    return render_template('upload.html', filename=filename)


# Routing function for the relations script to predict the relation between concepts
@app.route('/relationships')
def relationships():
    from relations import readFile as relationReadFile
    filename = relationReadFile('temp.nt', context)
    return render_template('upload.html', filename=filename)


# Routing function for the semantic similarity script. 
@app.route('/semanticSimilarity')
def semanticSimilarity():
    from semanticSimi import readFile as semanticReadFile
    filename = semanticReadFile('temp.nt', context)
    return render_template('upload.html', filename=filename)


# Routing function for the related images page (ImageNet) a URL of images
@app.route('/relImages')
def relImages():
    from relatedImages import readFile as relatedReadFile
    filename = relatedReadFile('temp.nt', context)
    return render_template('upload.html', filename=filename)


# Routing function for the pure images script (3 pure images of each concept)
@app.route('/pImages')
def pImages():
    from pureImages import readFile as pureReadFile
    filename = pureReadFile('temp.nt', context)
    return render_template('upload.html', filename=filename)


# Add all the features with a single click (relations, semantic similarity, related and pure images)
@app.route('/allfeatures')
def allfeatures():
    from pureImages import readFile as pureReadFile
    filename = pureReadFile('temp.nt', context)
    return render_template('upload.html', filename=filename)


# Routing function for downloading the file when a user clicks download file
@app.route('/database_download', methods=['GET', 'POST'])
def download_file():
    if request.method == 'POST':
        text = request.form['text']
        text = text.replace("&lt;", '<').replace('&gt;', '>').replace("</br>", "\n")
        response = make_response(text)
        response.headers["Content-Disposition"] = "attachment; filename=result.txt"
        return response
        render_template('upload.html')
    else:
        render_template('upload.html')

    render_template('upload.html')


# Routing function for index page (main)
@app.route('/')
def hello_world():
    return render_template('index.html')


# Routing function for about us
@app.route('/aboutUs')
def aboutUs():
    return render_template('aboutUs.html')


# Routing function for redirecting the triples from the main to SPARQL
def readFileQuery():
    data = ''
    os.system('cp output.nq files/input.nq')
    with open('files/input.nq') as reader:
        data = reader.read()
        data = data.split('\n')
    return data


# Routing function for storing the result
def readFileResult():
    data = ''
    with open('output.nq') as reader:
        data = reader.read()
        data = data.split('\n')
    return data


# Routing function for SPARQL page
@app.route('/queryOutput', methods=['GET', 'POST'])
def queryOutput():
    data = readFileQuery()
    return render_template('queryOutput.html', data=data)


# Routing function for Apache Jena to start the engine when a query is given
@app.route('/queryData', methods=['GET', 'POST'])
def queryData():
    if request.method == 'POST':
        try:
            data = None
            os.chdir(os.path.join(dir_path, 'files'))
            query = request.form['text']
            writer = open('query.sparql', 'w+')
            writer.write(query)
            writer.flush()
            writer.close()
            if 'outFinal' in os.listdir():
                shutil.rmtree('outFinal')
            os.system('./../apache-jena-3.13.1/bin/tdbloader2 --loc outFinal input.nq')
            os.system('./../apache-jena-3.13.1/bin/tdbquery --loc outFinal --query query.sparql > output.nq')
            data = readFileResult()
        except Exception as e:
            print(e)
        if not data:
            data = 'You entered an empty or a wrong query! Please try again ...'
            return render_template('queryOutput.html', data1=data)
    return render_template('queryOutput.html', data=data)


# Routing function to download SPARQL output
@app.route('/downloadData', methods=['GET', 'POST'])
def downloadData():
    if request.method == 'POST':
        os.chdir(dir_path)
        data1 = ''
        with open('files/output.nq') as reader:
            data1 = reader.read().replace('&lt', '<').replace('&gt', '>').replace('<br>', '\n')
        return send_file('files/output.nq', as_attachment=True)
        render_template('queryOutput.html')
    else:
        render_template('queryOutput.html')
    render_template('queryOutput.html')


@app.route('/output_Data')
def output_Data():
    data = readFileResult()
    return render_template('output.html', data=data)


# Load the models and render host 0.0.0.0 to 127.0.0.1 in docker
if __name__ == '__main__':
    prepare_Models()
    app.run(use_reloader=False, host='0.0.0.0')
