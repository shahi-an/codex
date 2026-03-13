pipeline {

 agent any

 environment {
  REGISTRY = "34.30.178.105:9082"
  IMAGE = "maid-app:v1"
 }

 stages {

  stage('Build Docker Image') {
   steps {
    sh 'docker build -t $IMAGE .'
   }
  }

  stage('Tag Image') {
   steps {
    sh 'docker tag $IMAGE $REGISTRY/$IMAGE:${BUILD_NUMBER}'
   }
  }

  stage('Push Image') {
   steps {
    sh 'docker push $REGISTRY/$IMAGE:${BUILD_NUMBER}'
   }
  }

 }

}

